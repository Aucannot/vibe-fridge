import 'package:sqflite/sqflite.dart';
import 'package:uuid/uuid.dart';

import '../models/inventory_item.dart';
import '../models/inventory_stats.dart';
import '../models/item_status.dart';
import '../models/item_wiki.dart';
import '../models/item_wiki_category.dart';
import '../models/registered_item.dart';
import 'app_database.dart';

class InventoryRepository {
  InventoryRepository(this._appDatabase);

  final AppDatabase _appDatabase;
  final _uuid = const Uuid();

  Database get _db => _appDatabase.database;

  Future<void> seedDefaults() {
    return _appDatabase.seedDefaults();
  }

  Future<List<ItemWikiCategory>> getCategories() async {
    final rows = await _db.query(
      'item_wiki_categories',
      orderBy: 'sort_order ASC, name ASC',
    );
    return rows.map(ItemWikiCategory.fromMap).toList();
  }

  Future<List<RegisteredItem>> getRegisteredItems({
    String? categoryId,
    String? keyword,
  }) async {
    final args = <Object?>[ItemStatus.active.dbValue];
    final where = <String>[];

    if (categoryId != null && categoryId.isNotEmpty) {
      where.add('w.category_id = ?');
      args.add(categoryId);
    }
    if (keyword != null && keyword.trim().isNotEmpty) {
      where.add('(w.name LIKE ? OR w.description LIKE ?)');
      final term = '%${keyword.trim()}%';
      args
        ..add(term)
        ..add(term);
    }

    final rows = await _db.rawQuery('''
      SELECT
        w.id AS wiki_id,
        w.name,
        w.icon,
        w.description,
        w.category_id,
        w.default_unit,
        w.storage_location,
        c.name AS category_name,
        COUNT(i.id) AS active_batch_count,
        COALESCE(SUM(i.quantity), 0) AS total_quantity,
        MIN(i.expiry_date) AS next_expiry_date
      FROM item_wikis w
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      LEFT JOIN items i ON i.wiki_id = w.id AND i.status = ?
      ${where.isEmpty ? '' : 'WHERE ${where.join(' AND ')}'}
      GROUP BY w.id
      ORDER BY w.name COLLATE NOCASE ASC
    ''', args);

    return rows.map(RegisteredItem.fromMap).toList();
  }

  Future<List<InventoryItem>> getActiveItems({int limit = 100}) async {
    final rows = await _db.rawQuery('''
      SELECT
        i.*,
        w.icon AS wiki_icon,
        c.name AS category_name
      FROM items i
      LEFT JOIN item_wikis w ON w.id = i.wiki_id
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      WHERE i.status = ?
      ORDER BY i.expiry_date IS NULL ASC, i.expiry_date ASC, i.created_at DESC
      LIMIT ?
    ''', [ItemStatus.active.dbValue, limit]);
    return rows.map(InventoryItem.fromMap).toList();
  }

  Future<List<InventoryItem>> getExpiringItems({int days = 7}) async {
    final today = _dateOnly(DateTime.now());
    final threshold = today.add(Duration(days: days));
    final rows = await _db.rawQuery('''
      SELECT
        i.*,
        w.icon AS wiki_icon,
        c.name AS category_name
      FROM items i
      LEFT JOIN item_wikis w ON w.id = i.wiki_id
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      WHERE i.status = ?
        AND i.expiry_date IS NOT NULL
        AND i.expiry_date >= ?
        AND i.expiry_date <= ?
      ORDER BY i.expiry_date ASC
    ''', [
      ItemStatus.active.dbValue,
      today.toIso8601String(),
      threshold.toIso8601String(),
    ]);
    return rows.map(InventoryItem.fromMap).toList();
  }

  Future<List<InventoryItem>> getHistoryItems({int limit = 100}) async {
    final today = _dateOnly(DateTime.now());
    final rows = await _db.rawQuery('''
      SELECT
        i.*,
        w.icon AS wiki_icon,
        c.name AS category_name
      FROM items i
      LEFT JOIN item_wikis w ON w.id = i.wiki_id
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      WHERE i.status IN (?, ?, ?)
        OR (
          i.status != ?
          AND i.expiry_date IS NOT NULL
          AND i.expiry_date < ?
        )
      ORDER BY
        CASE WHEN i.consumed_at IS NULL THEN 1 ELSE 0 END,
        i.consumed_at DESC,
        i.expiry_date DESC
      LIMIT ?
    ''', [
      ItemStatus.consumed.dbValue,
      ItemStatus.expired.dbValue,
      ItemStatus.wasted.dbValue,
      ItemStatus.consumed.dbValue,
      today.toIso8601String(),
      limit,
    ]);
    return rows.map(InventoryItem.fromMap).toList();
  }

  Future<List<InventoryItem>> getInventoryByWikiId(String wikiId) async {
    final rows = await _db.rawQuery('''
      SELECT
        i.*,
        w.icon AS wiki_icon,
        c.name AS category_name
      FROM items i
      LEFT JOIN item_wikis w ON w.id = i.wiki_id
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      WHERE i.wiki_id = ?
      ORDER BY
        CASE i.status WHEN 'active' THEN 0 WHEN 'expired' THEN 1 ELSE 2 END,
        i.expiry_date IS NULL ASC,
        i.expiry_date ASC
    ''', [wikiId]);
    return rows.map(InventoryItem.fromMap).toList();
  }

  Future<InventoryItem?> getItem(String itemId) async {
    final rows = await _db.rawQuery('''
      SELECT
        i.*,
        w.icon AS wiki_icon,
        c.name AS category_name
      FROM items i
      LEFT JOIN item_wikis w ON w.id = i.wiki_id
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      WHERE i.id = ?
      LIMIT 1
    ''', [itemId]);
    if (rows.isEmpty) {
      return null;
    }
    return InventoryItem.fromMap(rows.first);
  }

  Future<ItemWiki?> getWiki(String wikiId) async {
    final rows = await _db.rawQuery('''
      SELECT
        w.*,
        c.name AS category_name,
        COUNT(i.id) AS inventory_count
      FROM item_wikis w
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      LEFT JOIN items i ON i.wiki_id = w.id AND i.status != ?
      WHERE w.id = ?
      GROUP BY w.id
      LIMIT 1
    ''', [ItemStatus.consumed.dbValue, wikiId]);
    if (rows.isEmpty) {
      return null;
    }
    return ItemWiki.fromMap(rows.first);
  }

  Future<InventoryStats> getStats() async {
    final today = _dateOnly(DateTime.now());
    final soon = today.add(const Duration(days: 7));
    final activeRows = await _db.rawQuery('''
      SELECT
        COUNT(*) AS active_batch_count,
        COALESCE(SUM(quantity), 0) AS total_quantity
      FROM items
      WHERE status = ?
    ''', [ItemStatus.active.dbValue]);

    final expiringSoon = Sqflite.firstIntValue(await _db.rawQuery('''
      SELECT COUNT(*)
      FROM items
      WHERE status = ?
        AND expiry_date IS NOT NULL
        AND expiry_date >= ?
        AND expiry_date <= ?
    ''', [
      ItemStatus.active.dbValue,
      today.toIso8601String(),
      soon.toIso8601String(),
    ]));

    final expired = Sqflite.firstIntValue(await _db.rawQuery('''
      SELECT COUNT(*)
      FROM items
      WHERE status != ?
        AND expiry_date IS NOT NULL
        AND expiry_date < ?
    ''', [
      ItemStatus.consumed.dbValue,
      today.toIso8601String(),
    ]));

    final wikis = Sqflite.firstIntValue(
      await _db.rawQuery('SELECT COUNT(*) FROM item_wikis'),
    );

    final reminders = Sqflite.firstIntValue(await _db.rawQuery('''
      SELECT COUNT(*)
      FROM items
      WHERE status = ?
        AND is_reminder_enabled = 1
        AND reminder_date IS NOT NULL
        AND reminder_date <= ?
    ''', [
      ItemStatus.active.dbValue,
      today.toIso8601String(),
    ]));

    final categoryRows = await _db.rawQuery('''
      SELECT c.name AS category_name, COALESCE(SUM(i.quantity), 0) AS total_count
      FROM item_wiki_categories c
      LEFT JOIN item_wikis w ON w.category_id = c.id
      LEFT JOIN items i ON i.wiki_id = w.id AND i.status = ?
      GROUP BY c.id
      HAVING total_count > 0
      ORDER BY c.sort_order ASC
    ''', [ItemStatus.active.dbValue]);

    final active = activeRows.first;
    return InventoryStats(
      activeBatchCount: (active['active_batch_count'] as int?) ?? 0,
      totalQuantity: (active['total_quantity'] as int?) ?? 0,
      expiringSoonCount: expiringSoon ?? 0,
      expiredCount: expired ?? 0,
      registeredWikiCount: wikis ?? 0,
      needingReminderCount: reminders ?? 0,
      categoryCounts: categoryRows
          .map(
            (row) => CategoryCount(
              categoryName: row['category_name'] as String,
              count: (row['total_count'] as int?) ?? 0,
            ),
          )
          .toList(),
    );
  }

  Future<void> createItem({
    required String name,
    String? categoryId,
    String? description,
    int quantity = 1,
    String? unit,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    int reminderDaysBefore = 3,
  }) async {
    final normalizedName = name.trim();
    if (normalizedName.isEmpty) {
      throw ArgumentError('物品名称不能为空');
    }
    if (quantity <= 0) {
      throw ArgumentError('数量必须大于 0');
    }

    final now = DateTime.now();
    final nowText = now.toIso8601String();
    final reminderDate = expiryDate == null
        ? null
        : _dateOnly(expiryDate).subtract(Duration(days: reminderDaysBefore));

    await _db.transaction((txn) async {
      final existing = await txn.query(
        'item_wikis',
        where: 'lower(name) = lower(?)',
        whereArgs: [normalizedName],
        limit: 1,
      );

      late final String wikiId;
      if (existing.isEmpty) {
        wikiId = _uuid.v4();
        await txn.insert('item_wikis', {
          'id': wikiId,
          'name': normalizedName,
          'icon': null,
          'description': description,
          'category_id': categoryId,
          'default_unit': unit,
          'suggested_expiry_days': null,
          'storage_location': null,
          'notes': null,
          'image_path': null,
          'created_at': nowText,
          'updated_at': nowText,
        });
      } else {
        wikiId = existing.first['id'] as String;
        if (categoryId != null || unit != null || description != null) {
          await txn.update(
            'item_wikis',
            {
              if (categoryId != null) 'category_id': categoryId,
              if (unit != null && unit.trim().isNotEmpty) 'default_unit': unit,
              if (description != null && description.trim().isNotEmpty)
                'description': description,
              'updated_at': nowText,
            },
            where: 'id = ?',
            whereArgs: [wikiId],
          );
        }
      }

      await txn.insert('items', {
        'id': _uuid.v4(),
        'wiki_id': wikiId,
        'name': normalizedName,
        'description': description,
        'quantity': quantity,
        'unit': unit,
        'purchase_date': _dateText(purchaseDate),
        'expiry_date': _dateText(expiryDate),
        'reminder_date': _dateText(reminderDate),
        'status': ItemStatus.active.dbValue,
        'is_reminder_enabled': 1,
        'consumed_at': null,
        'predicted_expiry_date': null,
        'prediction_confidence': null,
        'image_path': null,
        'source_app': null,
        'source_order_id': null,
        'created_at': nowText,
        'updated_at': nowText,
      });
    });
  }

  Future<void> updateItemQuantity(String itemId, int delta) async {
    final item = await getItem(itemId);
    if (item == null) {
      return;
    }
    final nextQuantity = item.quantity + delta;
    if (nextQuantity <= 0) {
      await markAsConsumed(itemId);
      return;
    }
    await _db.update(
      'items',
      {
        'quantity': nextQuantity,
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [itemId],
    );
  }

  Future<void> updateItem({
    required String itemId,
    required int quantity,
    String? unit,
    String? description,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    bool isReminderEnabled = true,
    int reminderDaysBefore = 3,
  }) async {
    if (quantity <= 0) {
      throw ArgumentError('数量必须大于 0');
    }
    final reminderDate = expiryDate == null
        ? null
        : _dateOnly(expiryDate).subtract(Duration(days: reminderDaysBefore));
    await _db.update(
      'items',
      {
        'quantity': quantity,
        'unit': _blankToNull(unit),
        'description': _blankToNull(description),
        'purchase_date': _dateText(purchaseDate),
        'expiry_date': _dateText(expiryDate),
        'reminder_date': _dateText(reminderDate),
        'is_reminder_enabled': isReminderEnabled ? 1 : 0,
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [itemId],
    );
  }

  Future<void> deleteItem(String itemId) async {
    await _db.delete('items', where: 'id = ?', whereArgs: [itemId]);
  }

  Future<void> restoreItem(String itemId) async {
    await _db.update(
      'items',
      {
        'status': ItemStatus.active.dbValue,
        'consumed_at': null,
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [itemId],
    );
  }

  Future<void> markAsConsumed(String itemId) async {
    final item = await getItem(itemId);
    if (item == null) {
      return;
    }
    final now = DateTime.now();
    final nowText = now.toIso8601String();
    if (item.quantity > 1) {
      await _db.transaction((txn) async {
        await txn.update(
          'items',
          {
            'quantity': item.quantity - 1,
            'updated_at': nowText,
          },
          where: 'id = ?',
          whereArgs: [item.id],
        );
        final consumed = item
            .copyWith(
              quantity: 1,
              status: ItemStatus.consumed,
              consumedAt: now,
            )
            .toMap();
        consumed['id'] = _uuid.v4();
        consumed['status'] = ItemStatus.consumed.dbValue;
        consumed['consumed_at'] = nowText;
        consumed['created_at'] = nowText;
        consumed['updated_at'] = nowText;
        await txn.insert('items', consumed);
      });
    } else {
      await _db.update(
        'items',
        {
          'status': ItemStatus.consumed.dbValue,
          'consumed_at': nowText,
          'updated_at': nowText,
        },
        where: 'id = ?',
        whereArgs: [item.id],
      );
    }
  }

  Future<void> updateWiki({
    required String wikiId,
    required String name,
    String? categoryId,
    String? icon,
    String? description,
    String? defaultUnit,
    int? suggestedExpiryDays,
    String? storageLocation,
    String? notes,
  }) async {
    final normalizedName = name.trim();
    if (normalizedName.isEmpty) {
      throw ArgumentError('Wiki 名称不能为空');
    }
    if (suggestedExpiryDays != null && suggestedExpiryDays <= 0) {
      throw ArgumentError('建议保质期必须大于 0');
    }

    await _db.transaction((txn) async {
      await txn.update(
        'item_wikis',
        {
          'name': normalizedName,
          'category_id': categoryId,
          'icon': _blankToNull(icon),
          'description': _blankToNull(description),
          'default_unit': _blankToNull(defaultUnit),
          'suggested_expiry_days': suggestedExpiryDays,
          'storage_location': _blankToNull(storageLocation),
          'notes': _blankToNull(notes),
          'updated_at': DateTime.now().toIso8601String(),
        },
        where: 'id = ?',
        whereArgs: [wikiId],
      );
      await txn.update(
        'items',
        {
          'name': normalizedName,
          'updated_at': DateTime.now().toIso8601String(),
        },
        where: 'wiki_id = ?',
        whereArgs: [wikiId],
      );
    });
  }

  Future<int> getWikiInventoryCount(String wikiId) async {
    return Sqflite.firstIntValue(
          await _db.rawQuery(
            'SELECT COUNT(*) FROM items WHERE wiki_id = ?',
            [wikiId],
          ),
        ) ??
        0;
  }

  Future<void> deleteWiki(String wikiId, {bool force = false}) async {
    final count = await getWikiInventoryCount(wikiId);
    if (count > 0 && !force) {
      throw StateError('该 Wiki 下还有库存记录，无法删除');
    }
    await _db.delete('item_wikis', where: 'id = ?', whereArgs: [wikiId]);
  }

  Future<LegacyImportResult> importLegacyData(Map<String, dynamic> payload) async {
    final categories = _payloadList(payload['categories']);
    final wikis = _payloadList(payload['wikis']);
    final items = _payloadList(payload['items']);
    final tags = _payloadList(payload['tags']);
    final itemTags = _payloadList(payload['item_tags']);
    final nowText = DateTime.now().toIso8601String();

    var importedCategories = 0;
    var importedWikis = 0;
    var importedItems = 0;
    var importedTags = 0;
    var importedItemTags = 0;

    await _db.transaction((txn) async {
      final categoryIdMap = <String, String>{};
      for (final row in categories) {
        final oldId = _requiredText(row['id'], fallback: _uuid.v4());
        final name = _requiredText(row['name'], fallback: '其他');
        final existingById = await txn.query(
          'item_wiki_categories',
          columns: ['id'],
          where: 'id = ?',
          whereArgs: [oldId],
          limit: 1,
        );
        if (existingById.isNotEmpty) {
          categoryIdMap[oldId] = oldId;
          continue;
        }

        final existingByName = await txn.query(
          'item_wiki_categories',
          columns: ['id'],
          where: 'name = ?',
          whereArgs: [name],
          limit: 1,
        );
        if (existingByName.isNotEmpty) {
          categoryIdMap[oldId] = existingByName.first['id'] as String;
          continue;
        }

        await txn.insert('item_wiki_categories', {
          'id': oldId,
          'name': name,
          'icon': _blankToNull(row['icon'] as String?),
          'color': _blankToNull(row['color'] as String?),
          'sort_order': _intValue(row['sort_order'], fallback: 0),
          'created_at': _requiredText(row['created_at'], fallback: nowText),
          'updated_at': _requiredText(row['updated_at'], fallback: nowText),
        });
        categoryIdMap[oldId] = oldId;
        importedCategories += 1;
      }

      final wikiIdMap = <String, String>{};
      for (final row in wikis) {
        final oldId = _requiredText(row['id'], fallback: _uuid.v4());
        final name = _requiredText(row['name'], fallback: '未命名物品');
        final categoryId = row['category_id'] == null
            ? null
            : categoryIdMap[row['category_id'] as String] ?? row['category_id'] as String;
        final data = {
          'name': name,
          'icon': _blankToNull(row['icon'] as String?),
          'description': _blankToNull(row['description'] as String?),
          'category_id': categoryId,
          'default_unit': _blankToNull(row['default_unit'] as String?),
          'suggested_expiry_days': _nullableInt(row['suggested_expiry_days']),
          'storage_location': _blankToNull(row['storage_location'] as String?),
          'notes': _blankToNull(row['notes'] as String?),
          'image_path': _blankToNull(row['image_path'] as String?),
          'updated_at': _requiredText(row['updated_at'], fallback: nowText),
        };

        final existingById = await txn.query(
          'item_wikis',
          columns: ['id'],
          where: 'id = ?',
          whereArgs: [oldId],
          limit: 1,
        );
        if (existingById.isNotEmpty) {
          wikiIdMap[oldId] = oldId;
          await txn.update('item_wikis', data, where: 'id = ?', whereArgs: [oldId]);
          continue;
        }

        final existingByName = await txn.query(
          'item_wikis',
          columns: ['id'],
          where: 'lower(name) = lower(?)',
          whereArgs: [name],
          limit: 1,
        );
        if (existingByName.isNotEmpty) {
          final existingId = existingByName.first['id'] as String;
          wikiIdMap[oldId] = existingId;
          await txn.update('item_wikis', data, where: 'id = ?', whereArgs: [existingId]);
          continue;
        }

        await txn.insert('item_wikis', {
          'id': oldId,
          ...data,
          'created_at': _requiredText(row['created_at'], fallback: nowText),
        });
        wikiIdMap[oldId] = oldId;
        importedWikis += 1;
      }

      for (final row in items) {
        final oldId = _requiredText(row['id'], fallback: _uuid.v4());
        final existing = await txn.query(
          'items',
          columns: ['id'],
          where: 'id = ?',
          whereArgs: [oldId],
          limit: 1,
        );
        if (existing.isNotEmpty) {
          continue;
        }

        final oldWikiId = row['wiki_id'] as String?;
        final wikiId = oldWikiId == null ? null : wikiIdMap[oldWikiId] ?? oldWikiId;
        if (wikiId == null) {
          continue;
        }

        await txn.insert('items', {
          'id': oldId,
          'wiki_id': wikiId,
          'name': _requiredText(row['name'], fallback: '未命名物品'),
          'description': _blankToNull(row['description'] as String?),
          'quantity': _intValue(row['quantity'], fallback: 1),
          'unit': _blankToNull(row['unit'] as String?),
          'purchase_date': _blankToNull(row['purchase_date'] as String?),
          'expiry_date': _blankToNull(row['expiry_date'] as String?),
          'reminder_date': _blankToNull(row['reminder_date'] as String?),
          'status': ItemStatus.fromDbValue(row['status'] as String?).dbValue,
          'is_reminder_enabled': _boolAsInt(row['is_reminder_enabled']),
          'consumed_at': _blankToNull(row['consumed_at'] as String?),
          'predicted_expiry_date': _blankToNull(row['predicted_expiry_date'] as String?),
          'prediction_confidence': (row['prediction_confidence'] as num?)?.toDouble(),
          'image_path': _blankToNull(row['image_path'] as String?),
          'source_app': _blankToNull(row['source_app'] as String?),
          'source_order_id': _blankToNull(row['source_order_id'] as String?),
          'created_at': _requiredText(row['created_at'], fallback: nowText),
          'updated_at': _requiredText(row['updated_at'], fallback: nowText),
        });
        importedItems += 1;
      }

      final tagIdMap = <String, String>{};
      for (final row in tags) {
        final oldId = _requiredText(row['id'], fallback: _uuid.v4());
        final name = _blankToNull(row['name'] as String?);
        if (name == null) {
          continue;
        }
        final existingById = await txn.query(
          'tags',
          columns: ['id'],
          where: 'id = ?',
          whereArgs: [oldId],
          limit: 1,
        );
        if (existingById.isNotEmpty) {
          tagIdMap[oldId] = oldId;
          continue;
        }
        final existingByName = await txn.query(
          'tags',
          columns: ['id'],
          where: 'name = ?',
          whereArgs: [name],
          limit: 1,
        );
        if (existingByName.isNotEmpty) {
          tagIdMap[oldId] = existingByName.first['id'] as String;
          continue;
        }
        await txn.insert('tags', {
          'id': oldId,
          'name': name,
          'color': _blankToNull(row['color'] as String?),
          'created_at': _requiredText(row['created_at'], fallback: nowText),
        });
        tagIdMap[oldId] = oldId;
        importedTags += 1;
      }

      for (final row in itemTags) {
        final itemId = row['item_id'] as String?;
        final oldTagId = row['tag_id'] as String?;
        if (itemId == null || oldTagId == null) {
          continue;
        }
        final tagId = tagIdMap[oldTagId] ?? oldTagId;
        await txn.insert(
          'item_tags',
          {
            'item_id': itemId,
            'tag_id': tagId,
            'created_at': _requiredText(row['created_at'], fallback: nowText),
          },
          conflictAlgorithm: ConflictAlgorithm.ignore,
        );
        importedItemTags += 1;
      }
    });

    return LegacyImportResult(
      categories: importedCategories,
      wikis: importedWikis,
      items: importedItems,
      tags: importedTags,
      itemTags: importedItemTags,
    );
  }
}

class LegacyImportResult {
  const LegacyImportResult({
    required this.categories,
    required this.wikis,
    required this.items,
    required this.tags,
    required this.itemTags,
  });

  final int categories;
  final int wikis;
  final int items;
  final int tags;
  final int itemTags;

  int get total => categories + wikis + items + tags + itemTags;
}

DateTime _dateOnly(DateTime value) {
  return DateTime(value.year, value.month, value.day);
}

String? _dateText(DateTime? value) {
  if (value == null) {
    return null;
  }
  return _dateOnly(value).toIso8601String();
}

String? _blankToNull(String? value) {
  final trimmed = value?.trim();
  if (trimmed == null || trimmed.isEmpty) {
    return null;
  }
  return trimmed;
}

List<Map<String, dynamic>> _payloadList(Object? value) {
  if (value is! List) {
    return [];
  }
  return value.whereType<Map>().map((row) => Map<String, dynamic>.from(row)).toList();
}

String _requiredText(Object? value, {required String fallback}) {
  if (value is String && value.trim().isNotEmpty) {
    return value.trim();
  }
  return fallback;
}

int _intValue(Object? value, {required int fallback}) {
  if (value is int) {
    return value;
  }
  if (value is num) {
    return value.toInt();
  }
  if (value is String) {
    return int.tryParse(value) ?? fallback;
  }
  return fallback;
}

int? _nullableInt(Object? value) {
  if (value == null) {
    return null;
  }
  if (value is int) {
    return value;
  }
  if (value is num) {
    return value.toInt();
  }
  if (value is String && value.trim().isNotEmpty) {
    return int.tryParse(value);
  }
  return null;
}

int _boolAsInt(Object? value) {
  if (value is bool) {
    return value ? 1 : 0;
  }
  if (value is int) {
    return value == 0 ? 0 : 1;
  }
  if (value is String) {
    return value == '0' || value.toLowerCase() == 'false' ? 0 : 1;
  }
  return 1;
}
