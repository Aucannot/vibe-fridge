import 'dart:convert';

import 'package:sqflite/sqflite.dart';
import 'package:uuid/uuid.dart';

import '../models/inventory_item.dart';
import '../models/inventory_stats.dart';
import '../models/item_status.dart';
import '../models/item_wiki.dart';
import '../models/item_wiki_category.dart';
import '../models/registered_item.dart';
import '../models/shopping_list_item.dart';
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
        c.name AS category_name,
        (
          SELECT GROUP_CONCAT(t.name, '||')
          FROM item_tags it
          JOIN tags t ON t.id = it.tag_id
          WHERE it.item_id = i.id
        ) AS tag_names
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
        c.name AS category_name,
        (
          SELECT GROUP_CONCAT(t.name, '||')
          FROM item_tags it
          JOIN tags t ON t.id = it.tag_id
          WHERE it.item_id = i.id
        ) AS tag_names
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

  Future<List<InventoryItem>> getTodayActionItems({int limit = 20}) async {
    final today = _dateOnly(DateTime.now());
    final tomorrow = today.add(const Duration(days: 1));
    final todayText = today.toIso8601String();
    final tomorrowText = tomorrow.toIso8601String();
    final rows = await _db.rawQuery('''
      SELECT
        i.*,
        w.icon AS wiki_icon,
        c.name AS category_name,
        (
          SELECT GROUP_CONCAT(t.name, '||')
          FROM item_tags it
          JOIN tags t ON t.id = it.tag_id
          WHERE it.item_id = i.id
        ) AS tag_names
      FROM items i
      LEFT JOIN item_wikis w ON w.id = i.wiki_id
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      WHERE i.status = ?
        AND (
          (i.expiry_date IS NOT NULL AND i.expiry_date <= ?)
          OR (
            i.is_reminder_enabled = 1
            AND i.reminder_date IS NOT NULL
            AND i.reminder_date <= ?
          )
        )
        AND NOT EXISTS (
          SELECT 1
          FROM reminder_logs rl
          WHERE rl.item_id = i.id
            AND rl.reminder_type IN (?, ?)
            AND rl.sent_at >= ?
            AND rl.sent_at < ?
        )
      ORDER BY
        CASE
          WHEN i.expiry_date IS NOT NULL AND i.expiry_date < ? THEN 0
          WHEN i.expiry_date IS NOT NULL AND i.expiry_date = ? THEN 1
          ELSE 2
        END,
        i.expiry_date IS NULL ASC,
        i.expiry_date ASC,
        i.reminder_date ASC,
        i.created_at DESC
      LIMIT ?
    ''', [
      ItemStatus.active.dbValue,
      todayText,
      todayText,
      _reminderActionIgnored,
      _reminderActionSnoozed,
      todayText,
      tomorrowText,
      todayText,
      todayText,
      limit,
    ]);
    return rows.map(InventoryItem.fromMap).toList();
  }

  Future<List<PendingReminderNotification>> getPendingReminderNotifications({
    DateTime? now,
    int daysAhead = 14,
    int limit = 64,
  }) async {
    final timestamp = now ?? DateTime.now();
    final today = _dateOnly(timestamp);
    final tomorrow = today.add(const Duration(days: 1));
    final horizon = today.add(Duration(days: daysAhead + 1));
    final rows = await _db.rawQuery('''
      SELECT
        i.*,
        w.icon AS wiki_icon,
        c.name AS category_name,
        (
          SELECT GROUP_CONCAT(t.name, '||')
          FROM item_tags it
          JOIN tags t ON t.id = it.tag_id
          WHERE it.item_id = i.id
        ) AS tag_names
      FROM items i
      LEFT JOIN item_wikis w ON w.id = i.wiki_id
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      WHERE i.status = ?
        AND i.is_reminder_enabled = 1
        AND i.reminder_date IS NOT NULL
        AND i.reminder_date <= ?
        AND NOT EXISTS (
          SELECT 1
          FROM reminder_logs rl
          WHERE rl.item_id = i.id
            AND rl.reminder_type IN (?, ?)
            AND rl.sent_at >= ?
            AND rl.sent_at < ?
        )
      ORDER BY i.reminder_date ASC, i.expiry_date ASC, i.created_at DESC
      LIMIT ?
    ''', [
      ItemStatus.active.dbValue,
      horizon.toIso8601String(),
      _reminderActionIgnored,
      _reminderActionSnoozed,
      today.toIso8601String(),
      tomorrow.toIso8601String(),
      limit,
    ]);

    return rows
        .map(InventoryItem.fromMap)
        .map((item) => PendingReminderNotification.fromItem(item, timestamp))
        .toList();
  }

  Future<List<InventoryItem>> getHistoryItems({int limit = 100}) async {
    final today = _dateOnly(DateTime.now());
    final rows = await _db.rawQuery('''
      SELECT
        i.*,
        w.icon AS wiki_icon,
        c.name AS category_name,
        (
          SELECT GROUP_CONCAT(t.name, '||')
          FROM item_tags it
          JOIN tags t ON t.id = it.tag_id
          WHERE it.item_id = i.id
        ) AS tag_names
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

  Future<List<ShoppingListItem>> getShoppingListItems({
    bool includeConverted = false,
  }) async {
    final rows = await _db.rawQuery('''
      SELECT
        s.*,
        c.name AS category_name
      FROM shopping_list_items s
      LEFT JOIN item_wiki_categories c ON c.id = s.category_id
      WHERE (? = 1 OR s.converted_at IS NULL)
      ORDER BY
        s.is_checked ASC,
        c.sort_order ASC,
        c.name ASC,
        s.updated_at DESC
    ''', [includeConverted ? 1 : 0]);
    return rows.map(ShoppingListItem.fromMap).toList();
  }

  Future<List<ShoppingSuggestion>> getShoppingSuggestions({
    int limit = 8,
  }) async {
    final rows = await _db.rawQuery('''
      SELECT
        w.id AS wiki_id,
        w.name,
        w.category_id,
        w.default_unit,
        c.name AS category_name,
        c.icon AS category_icon,
        COUNT(i.id) AS total_records,
        COALESCE(
          SUM(CASE WHEN i.status = ? THEN i.quantity ELSE 0 END),
          0
        ) AS active_quantity,
        COALESCE(
          SUM(CASE WHEN i.status = ? THEN 1 ELSE 0 END),
          0
        ) AS consumed_count,
        MAX(
          CASE WHEN i.status = ? THEN i.consumed_at ELSE NULL END
        ) AS last_consumed_at
      FROM item_wikis w
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      LEFT JOIN items i ON i.wiki_id = w.id
      WHERE NOT EXISTS (
        SELECT 1
        FROM shopping_list_items s
        WHERE s.converted_at IS NULL
          AND (
            s.source_wiki_id = w.id
            OR lower(s.name) = lower(w.name)
          )
      )
      GROUP BY w.id
      HAVING
        (
          active_quantity <= 1
          AND total_records > 0
        )
        OR consumed_count >= 2
      ORDER BY
        CASE
          WHEN active_quantity = 0 AND consumed_count > 0 THEN 0
          WHEN active_quantity <= 1 THEN 1
          ELSE 2
        END,
        consumed_count DESC,
        last_consumed_at DESC,
        w.name COLLATE NOCASE ASC
      LIMIT ?
    ''', [
      ItemStatus.active.dbValue,
      ItemStatus.consumed.dbValue,
      ItemStatus.consumed.dbValue,
      limit,
    ]);
    return rows.map(ShoppingSuggestion.fromMap).toList();
  }

  Future<List<InventoryItem>> getInventoryByWikiId(String wikiId) async {
    final rows = await _db.rawQuery('''
      SELECT
        i.*,
        w.icon AS wiki_icon,
        c.name AS category_name,
        (
          SELECT GROUP_CONCAT(t.name, '||')
          FROM item_tags it
          JOIN tags t ON t.id = it.tag_id
          WHERE it.item_id = i.id
        ) AS tag_names
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
        c.name AS category_name,
        (
          SELECT GROUP_CONCAT(t.name, '||')
          FROM item_tags it
          JOIN tags t ON t.id = it.tag_id
          WHERE it.item_id = i.id
        ) AS tag_names
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

  Future<int> countOrderImportDuplicates({
    required String sourceOrderId,
    required String name,
    DateTime? purchaseDate,
  }) async {
    final normalizedOrderId = _blankToNull(sourceOrderId);
    final normalizedName = _blankToNull(name);
    if (normalizedOrderId == null || normalizedName == null) {
      return 0;
    }
    final where = StringBuffer('''
            SELECT COUNT(*)
            FROM items
            WHERE source_order_id = ?
              AND lower(name) = lower(?)
    ''');
    final args = <Object?>[
      normalizedOrderId,
      normalizedName,
    ];
    if (purchaseDate != null) {
      where.write(' AND purchase_date = ?');
      args.add(_dateText(purchaseDate));
    }
    return Sqflite.firstIntValue(
          await _db.rawQuery(where.toString(), args),
        ) ??
        0;
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
    bool syncDescriptionToWiki = true,
    int quantity = 1,
    String? unit,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    DateTime? predictedExpiryDate,
    double? predictionConfidence,
    double? recognitionConfidence,
    String? imagePath,
    String? storageLocation,
    List<String> tags = const [],
    String? sourceApp,
    String? sourceOrderId,
    String? importBatchId,
    int? reminderDaysBefore,
  }) async {
    final normalizedName = name.trim();
    if (normalizedName.isEmpty) {
      throw ArgumentError('物品名称不能为空');
    }
    _validateInventoryDraft(
      quantity: quantity,
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
      reminderDaysBefore: reminderDaysBefore,
      predictionConfidence: predictionConfidence,
      recognitionConfidence: recognitionConfidence,
    );

    final now = DateTime.now();
    final nowText = now.toIso8601String();
    await _db.transaction((txn) async {
      final existing = await txn.query(
        'item_wikis',
        where: 'lower(name) = lower(?)',
        whereArgs: [normalizedName],
        limit: 1,
      );

      late final String wikiId;
      late final int effectiveReminderDays;
      if (existing.isEmpty) {
        wikiId = _uuid.v4();
        effectiveReminderDays = reminderDaysBefore ?? 3;
        await txn.insert('item_wikis', {
          'id': wikiId,
          'name': normalizedName,
          'icon': null,
          'description': syncDescriptionToWiki ? description : null,
          'category_id': categoryId,
          'default_unit': unit,
          'suggested_expiry_days': null,
          'storage_location': _blankToNull(storageLocation),
          'default_reminder_days': effectiveReminderDays,
          'notes': null,
          'image_path': null,
          'created_at': nowText,
          'updated_at': nowText,
        });
      } else {
        wikiId = existing.first['id'] as String;
        effectiveReminderDays = reminderDaysBefore ??
            ((existing.first['default_reminder_days'] as int?) ?? 3);
        if (categoryId != null ||
            unit != null ||
            (syncDescriptionToWiki && description != null)) {
          await txn.update(
            'item_wikis',
            {
              if (categoryId != null) 'category_id': categoryId,
              if (unit != null && unit.trim().isNotEmpty) 'default_unit': unit,
              if (syncDescriptionToWiki &&
                  description != null &&
                  description.trim().isNotEmpty)
                'description': description,
              if (storageLocation != null && storageLocation.trim().isNotEmpty)
                'storage_location': storageLocation.trim(),
              'updated_at': nowText,
            },
            where: 'id = ?',
            whereArgs: [wikiId],
          );
        }
      }

      final reminderDate = expiryDate == null
          ? null
          : _dateOnly(expiryDate)
              .subtract(Duration(days: effectiveReminderDays));

      final itemId = _uuid.v4();
      await txn.insert('items', {
        'id': itemId,
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
        'reminder_days_before': effectiveReminderDays,
        'consumed_at': null,
        'predicted_expiry_date': _dateText(predictedExpiryDate),
        'prediction_confidence': predictionConfidence,
        'recognition_confidence': recognitionConfidence,
        'image_path': _blankToNull(imagePath),
        'storage_location': _blankToNull(storageLocation),
        'source_app': _blankToNull(sourceApp),
        'source_order_id': _blankToNull(sourceOrderId),
        'import_batch_id': _blankToNull(importBatchId),
        'created_at': nowText,
        'updated_at': nowText,
      });
      await _replaceItemTags(txn, itemId: itemId, tagNames: tags);
    });
    await _recordBackupRelevantChange(
      changedRows: 1,
      reason: '新增库存',
    );
  }

  Future<String> addShoppingListItem(ShoppingListDraft draft) async {
    final normalizedName = draft.name.trim();
    if (normalizedName.isEmpty) {
      throw ArgumentError('采购物品名称不能为空');
    }
    if (draft.quantity <= 0) {
      throw ArgumentError('采购数量必须大于 0');
    }

    final categoryId = await _shoppingCategoryId(
      categoryId: draft.categoryId,
      sourceWikiId: draft.sourceWikiId,
    );
    final normalizedUnit = _blankToNull(draft.unit);
    final normalizedNote = _blankToNull(draft.note);
    final normalizedSource = _blankToNull(draft.source) ?? 'manual';
    final nowText = DateTime.now().toIso8601String();

    final existing = await _db.query(
      'shopping_list_items',
      columns: ['id', 'quantity'],
      where: '''
        lower(name) = lower(?)
        AND COALESCE(category_id, '') = COALESCE(?, '')
        AND COALESCE(unit, '') = COALESCE(?, '')
        AND is_checked = 0
        AND converted_at IS NULL
      ''',
      whereArgs: [normalizedName, categoryId ?? '', normalizedUnit ?? ''],
      limit: 1,
    );
    if (existing.isNotEmpty) {
      final id = existing.first['id'] as String;
      final currentQuantity = (existing.first['quantity'] as int?) ?? 1;
      await _db.update(
        'shopping_list_items',
        {
          'quantity': currentQuantity + draft.quantity,
          if (normalizedNote != null) 'note': normalizedNote,
          'source': normalizedSource,
          if (draft.sourceWikiId != null) 'source_wiki_id': draft.sourceWikiId,
          if (draft.sourceItemId != null) 'source_item_id': draft.sourceItemId,
          'updated_at': nowText,
        },
        where: 'id = ?',
        whereArgs: [id],
      );
      return id;
    }

    final id = _uuid.v4();
    await _db.insert('shopping_list_items', {
      'id': id,
      'name': normalizedName,
      'category_id': categoryId,
      'source_wiki_id': _blankToNull(draft.sourceWikiId),
      'source_item_id': _blankToNull(draft.sourceItemId),
      'quantity': draft.quantity,
      'unit': normalizedUnit,
      'note': normalizedNote,
      'source': normalizedSource,
      'is_checked': 0,
      'checked_at': null,
      'converted_at': null,
      'created_at': nowText,
      'updated_at': nowText,
    });
    return id;
  }

  Future<String> addShoppingSuggestion(ShoppingSuggestion suggestion) {
    return addShoppingListItem(suggestion.toDraft());
  }

  Future<void> updateShoppingListItem({
    required String itemId,
    required ShoppingListDraft draft,
  }) async {
    final normalizedName = draft.name.trim();
    if (normalizedName.isEmpty) {
      throw ArgumentError('采购物品名称不能为空');
    }
    if (draft.quantity <= 0) {
      throw ArgumentError('采购数量必须大于 0');
    }
    final categoryId = await _shoppingCategoryId(
      categoryId: draft.categoryId,
      sourceWikiId: draft.sourceWikiId,
    );
    await _db.update(
      'shopping_list_items',
      {
        'name': normalizedName,
        'category_id': categoryId,
        'source_wiki_id': _blankToNull(draft.sourceWikiId),
        'source_item_id': _blankToNull(draft.sourceItemId),
        'quantity': draft.quantity,
        'unit': _blankToNull(draft.unit),
        'note': _blankToNull(draft.note),
        'source': _blankToNull(draft.source) ?? 'manual',
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ? AND converted_at IS NULL',
      whereArgs: [itemId],
    );
  }

  Future<void> setShoppingListItemChecked(
    String itemId, {
    required bool isChecked,
  }) async {
    await _db.update(
      'shopping_list_items',
      {
        'is_checked': isChecked ? 1 : 0,
        'checked_at': isChecked ? DateTime.now().toIso8601String() : null,
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ? AND converted_at IS NULL',
      whereArgs: [itemId],
    );
  }

  Future<void> deleteShoppingListItem(String itemId) async {
    await _db.delete(
      'shopping_list_items',
      where: 'id = ?',
      whereArgs: [itemId],
    );
  }

  Future<int> convertCheckedShoppingItemsToInventory({
    DateTime? purchaseDate,
    Iterable<String>? itemIds,
  }) async {
    final targetIds = itemIds
        ?.map((itemId) => itemId.trim())
        .where((itemId) => itemId.isNotEmpty)
        .toSet();
    final items = (await getShoppingListItems()).where(
      (item) {
        if (!item.isChecked || item.convertedAt != null) {
          return false;
        }
        return targetIds == null || targetIds.contains(item.id);
      },
    ).toList();
    var converted = 0;
    final boughtAt = purchaseDate ?? DateTime.now();
    for (final item in items) {
      await createItem(
        name: item.name,
        categoryId: item.categoryId,
        description: item.note,
        syncDescriptionToWiki: false,
        quantity: item.quantity,
        unit: item.unit,
        purchaseDate: boughtAt,
        sourceApp: '采购清单',
        importBatchId: 'shopping-list',
      );
      await _db.update(
        'shopping_list_items',
        {
          'converted_at': DateTime.now().toIso8601String(),
          'updated_at': DateTime.now().toIso8601String(),
        },
        where: 'id = ?',
        whereArgs: [item.id],
      );
      converted += 1;
    }
    return converted;
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
    final updated = await _db.update(
      'items',
      {
        'quantity': nextQuantity,
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [itemId],
    );
    await _recordBackupRelevantChange(
      changedRows: updated,
      reason: '更新库存数量',
    );
  }

  Future<void> updateItem({
    required String itemId,
    required int quantity,
    String? unit,
    String? description,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    String? imagePath,
    String? storageLocation,
    List<String>? tags,
    bool isReminderEnabled = true,
    int reminderDaysBefore = 3,
  }) async {
    _validateInventoryDraft(
      quantity: quantity,
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
      reminderDaysBefore: reminderDaysBefore,
    );
    final reminderDate = expiryDate == null
        ? null
        : _dateOnly(expiryDate).subtract(Duration(days: reminderDaysBefore));
    await _db.transaction((txn) async {
      await txn.update(
        'items',
        {
          'quantity': quantity,
          'unit': _blankToNull(unit),
          'description': _blankToNull(description),
          'purchase_date': _dateText(purchaseDate),
          'expiry_date': _dateText(expiryDate),
          'image_path': _blankToNull(imagePath),
          'storage_location': _blankToNull(storageLocation),
          'reminder_date': _dateText(reminderDate),
          'is_reminder_enabled': isReminderEnabled ? 1 : 0,
          'reminder_days_before': reminderDaysBefore,
          'updated_at': DateTime.now().toIso8601String(),
        },
        where: 'id = ?',
        whereArgs: [itemId],
      );
      if (tags != null) {
        await _replaceItemTags(txn, itemId: itemId, tagNames: tags);
      }
    });
    await _recordBackupRelevantChange(
      changedRows: 1,
      reason: '编辑库存',
    );
  }

  Future<String?> _shoppingCategoryId({
    String? categoryId,
    String? sourceWikiId,
  }) async {
    final directCategoryId = _blankToNull(categoryId);
    if (directCategoryId != null) {
      return directCategoryId;
    }
    final wikiId = _blankToNull(sourceWikiId);
    if (wikiId == null) {
      return null;
    }
    final rows = await _db.query(
      'item_wikis',
      columns: ['category_id'],
      where: 'id = ?',
      whereArgs: [wikiId],
      limit: 1,
    );
    if (rows.isEmpty) {
      return null;
    }
    return rows.first['category_id'] as String?;
  }

  Future<void> _replaceItemTags(
    DatabaseExecutor executor, {
    required String itemId,
    required List<String> tagNames,
  }) async {
    final normalizedNames = <String>[];
    final seen = <String>{};
    for (final tagName in tagNames) {
      final normalized = _blankToNull(tagName);
      if (normalized == null || seen.contains(normalized)) {
        continue;
      }
      seen.add(normalized);
      normalizedNames.add(normalized);
    }

    await executor.delete(
      'item_tags',
      where: 'item_id = ?',
      whereArgs: [itemId],
    );
    if (normalizedNames.isEmpty) {
      return;
    }

    final nowText = DateTime.now().toIso8601String();
    for (final tagName in normalizedNames) {
      final existing = await executor.query(
        'tags',
        columns: ['id'],
        where: 'name = ?',
        whereArgs: [tagName],
        limit: 1,
      );
      final tagId =
          existing.isNotEmpty ? existing.first['id'] as String : _uuid.v4();
      if (existing.isEmpty) {
        await executor.insert('tags', {
          'id': tagId,
          'name': tagName,
          'color': null,
          'created_at': nowText,
        });
      }
      await executor.insert(
        'item_tags',
        {
          'item_id': itemId,
          'tag_id': tagId,
          'created_at': nowText,
        },
        conflictAlgorithm: ConflictAlgorithm.ignore,
      );
    }
  }

  Future<void> deleteItem(String itemId) async {
    final deleted = await _db.delete(
      'items',
      where: 'id = ?',
      whereArgs: [itemId],
    );
    await _recordBackupRelevantChange(
      changedRows: deleted,
      reason: '删除库存',
    );
  }

  Future<void> deleteItems(Iterable<String> itemIds) async {
    final ids = _normalizeItemIds(itemIds);
    if (ids.isEmpty) {
      return;
    }
    final placeholders = List.filled(ids.length, '?').join(', ');
    final deleted = await _db.delete(
      'items',
      where: 'id IN ($placeholders)',
      whereArgs: ids,
    );
    await _recordBackupRelevantChange(
      changedRows: deleted,
      reason: '批量删除库存',
    );
  }

  Future<void> restoreItem(String itemId) async {
    final updated = await _db.update(
      'items',
      {
        'status': ItemStatus.active.dbValue,
        'consumed_at': null,
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [itemId],
    );
    await _recordBackupRelevantChange(
      changedRows: updated,
      reason: '恢复库存',
    );
  }

  Future<bool> recordReminderSentIfNeeded({
    required String itemId,
    required String reminderType,
    required String message,
    DateTime? now,
  }) async {
    final normalizedType = _blankToNull(reminderType);
    if (normalizedType == null) {
      throw ArgumentError('提醒类型不能为空');
    }
    final timestamp = now ?? DateTime.now();
    final today = _dateOnly(timestamp);
    final tomorrow = today.add(const Duration(days: 1));
    final sentToday = Sqflite.firstIntValue(
          await _db.rawQuery('''
            SELECT COUNT(*)
            FROM reminder_logs
            WHERE item_id = ?
              AND reminder_type = ?
              AND is_success = 1
              AND sent_at >= ?
              AND sent_at < ?
          ''', [
            itemId,
            normalizedType,
            today.toIso8601String(),
            tomorrow.toIso8601String(),
          ]),
        ) ??
        0;
    if (sentToday > 0) {
      return false;
    }
    await _insertReminderLog(
      itemId: itemId,
      reminderType: normalizedType,
      message: message,
      sentAt: timestamp,
    );
    return true;
  }

  Future<void> snoozeReminder(String itemId, {DateTime? now}) async {
    await _insertReminderLog(
      itemId: itemId,
      reminderType: _reminderActionSnoozed,
      message: '稍后提醒',
      sentAt: now ?? DateTime.now(),
    );
  }

  Future<void> ignoreReminderForToday(String itemId, {DateTime? now}) async {
    await _insertReminderLog(
      itemId: itemId,
      reminderType: _reminderActionIgnored,
      message: '忽略本次提醒',
      sentAt: now ?? DateTime.now(),
    );
  }

  Future<void> _insertReminderLog({
    required String itemId,
    required String reminderType,
    required String message,
    required DateTime sentAt,
  }) async {
    await _db.insert('reminder_logs', {
      'id': _uuid.v4(),
      'item_id': itemId,
      'reminder_type': reminderType,
      'message': message,
      'sent_at': sentAt.toIso8601String(),
      'is_success': 1,
      'error_message': null,
    });
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
    await _recordBackupRelevantChange(
      changedRows: 1,
      reason: '标记消耗',
    );
  }

  Future<void> markItemsAsConsumed(Iterable<String> itemIds) async {
    final ids = _normalizeItemIds(itemIds);
    for (final itemId in ids) {
      await markAsConsumed(itemId);
    }
  }

  Future<void> updateItemsStorageLocation(
    Iterable<String> itemIds,
    String? storageLocation,
  ) async {
    final ids = _normalizeItemIds(itemIds);
    if (ids.isEmpty) {
      return;
    }
    final placeholders = List.filled(ids.length, '?').join(', ');
    final updated = await _db.update(
      'items',
      {
        'storage_location': _blankToNull(storageLocation),
        'updated_at': DateTime.now().toIso8601String(),
      },
      where: 'id IN ($placeholders)',
      whereArgs: ids,
    );
    await _recordBackupRelevantChange(
      changedRows: updated,
      reason: '批量修改存放位置',
    );
  }

  Future<void> updateItemsCategory(
    Iterable<String> itemIds,
    String? categoryId,
  ) async {
    final ids = _normalizeItemIds(itemIds);
    if (ids.isEmpty) {
      return;
    }
    final placeholders = List.filled(ids.length, '?').join(', ');
    var updatedCount = 0;
    await _db.transaction((txn) async {
      final rows = await txn.rawQuery(
        'SELECT DISTINCT wiki_id FROM items WHERE id IN ($placeholders)',
        ids,
      );
      final wikiIds = rows
          .map((row) => row['wiki_id'] as String?)
          .whereType<String>()
          .toSet()
          .toList();
      if (wikiIds.isEmpty) {
        return;
      }
      final wikiPlaceholders = List.filled(wikiIds.length, '?').join(', ');
      updatedCount = await txn.update(
        'item_wikis',
        {
          'category_id': _blankToNull(categoryId),
          'updated_at': DateTime.now().toIso8601String(),
        },
        where: 'id IN ($wikiPlaceholders)',
        whereArgs: wikiIds,
      );
    });
    await _recordBackupRelevantChange(
      changedRows: updatedCount,
      reason: '批量修改分类',
    );
  }

  Future<void> updateWiki({
    required String wikiId,
    required String name,
    String? categoryId,
    String? icon,
    String? description,
    String? defaultUnit,
    int? suggestedExpiryDays,
    int? defaultReminderDays,
    String? storageLocation,
    String? notes,
  }) async {
    final normalizedName = name.trim();
    if (normalizedName.isEmpty) {
      throw ArgumentError('物品资料名称不能为空');
    }
    if (suggestedExpiryDays != null && suggestedExpiryDays <= 0) {
      throw ArgumentError('建议保质期必须大于 0');
    }
    if (defaultReminderDays != null && defaultReminderDays < 0) {
      throw ArgumentError('默认提醒提前天数不能小于 0');
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
          if (defaultReminderDays != null)
            'default_reminder_days': defaultReminderDays,
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
      throw StateError('该物品资料下还有库存记录，无法删除');
    }
    await _db.delete('item_wikis', where: 'id = ?', whereArgs: [wikiId]);
  }

  Future<LegacyImportPreview> previewLegacyImportData(
    Map<String, dynamic> payload,
  ) async {
    final categories = _payloadList(payload['categories']);
    final wikis = _payloadList(payload['wikis']);
    final items = _payloadList(payload['items']);
    final tags = _payloadList(payload['tags']);
    final itemTags = _payloadList(payload['item_tags']);

    var insertCategories = 0;
    var skipCategories = 0;
    var insertWikis = 0;
    var updateWikis = 0;
    var skipWikis = 0;
    var insertItems = 0;
    var updateItems = 0;
    var skipItems = 0;
    var insertTags = 0;
    var skipTags = 0;
    var insertItemTags = 0;
    var skipItemTags = 0;
    var failedRows = 0;
    final logs = <LegacyImportLogEntry>[];

    for (final row in categories) {
      final oldId = _requiredText(row['id'], fallback: _uuid.v4());
      final name = _requiredText(row['name'], fallback: '其他');
      final existingById = await _db.query(
        'item_wiki_categories',
        columns: ['id'],
        where: 'id = ?',
        whereArgs: [oldId],
        limit: 1,
      );
      if (existingById.isNotEmpty) {
        skipCategories += 1;
        logs.add(
          LegacyImportLogEntry.skipped(
            table: 'categories',
            name: name,
            reason: '分类已存在，将复用现有分类',
          ),
        );
        continue;
      }
      final existingByName = await _db.query(
        'item_wiki_categories',
        columns: ['id'],
        where: 'name = ?',
        whereArgs: [name],
        limit: 1,
      );
      if (existingByName.isNotEmpty) {
        skipCategories += 1;
        logs.add(
          LegacyImportLogEntry.skipped(
            table: 'categories',
            name: name,
            reason: '分类名称已存在，将按名称合并',
          ),
        );
        continue;
      }
      insertCategories += 1;
    }

    final knownWikiIds = <String>{};
    for (final row in wikis) {
      final oldId = _requiredText(row['id'], fallback: _uuid.v4());
      final name = _requiredText(row['name'], fallback: '未命名物品');
      final existing = await _findExistingWikiForLegacyRow(row);
      if (existing == null) {
        insertWikis += 1;
      } else if (_legacyRowIsNewer(row, existing)) {
        updateWikis += 1;
        logs.add(
          LegacyImportLogEntry.updated(
            table: 'wikis',
            name: name,
            reason: '匹配到现有物品资料，旧版记录较新',
          ),
        );
      } else {
        skipWikis += 1;
        logs.add(
          LegacyImportLogEntry.skipped(
            table: 'wikis',
            name: name,
            reason: '匹配到现有物品资料，现有资料更新或相同',
          ),
        );
      }
      knownWikiIds.add(oldId);
    }

    for (final row in items) {
      final name = _requiredText(row['name'], fallback: '未命名物品');
      final oldWikiId = row['wiki_id'] as String?;
      final hasKnownWiki = oldWikiId != null &&
          (knownWikiIds.contains(oldWikiId) || await _wikiExists(oldWikiId));
      if (!hasKnownWiki) {
        failedRows += 1;
        logs.add(
          LegacyImportLogEntry.failed(
            table: 'items',
            name: name,
            reason: '库存缺少可匹配的物品资料',
          ),
        );
        continue;
      }
      final existing = await _findExistingItemForLegacyRow(row);
      if (existing == null) {
        insertItems += 1;
      } else if (_legacyRowIsNewer(row, existing)) {
        updateItems += 1;
        logs.add(
          LegacyImportLogEntry.updated(
            table: 'items',
            name: name,
            reason: '匹配到现有库存，旧版记录较新',
          ),
        );
      } else {
        skipItems += 1;
        logs.add(
          LegacyImportLogEntry.skipped(
            table: 'items',
            name: name,
            reason: '按名称/日期识别为重复库存',
          ),
        );
      }
    }

    for (final row in tags) {
      final oldId = _requiredText(row['id'], fallback: _uuid.v4());
      final name = _blankToNull(row['name'] as String?);
      if (name == null) {
        failedRows += 1;
        logs.add(
          LegacyImportLogEntry.failed(
            table: 'tags',
            name: oldId,
            reason: '标签缺少名称',
          ),
        );
        continue;
      }
      final existingById = await _db.query(
        'tags',
        columns: ['id'],
        where: 'id = ?',
        whereArgs: [oldId],
        limit: 1,
      );
      final existingByName = existingById.isEmpty
          ? await _db.query(
              'tags',
              columns: ['id'],
              where: 'name = ?',
              whereArgs: [name],
              limit: 1,
            )
          : const <Map<String, Object?>>[];
      if (existingById.isNotEmpty || existingByName.isNotEmpty) {
        skipTags += 1;
        final reason = existingById.isNotEmpty ? '标签已存在' : '标签名称已存在';
        logs.add(
          LegacyImportLogEntry.skipped(
            table: 'tags',
            name: name,
            reason: reason,
          ),
        );
      } else {
        insertTags += 1;
      }
    }

    for (final row in itemTags) {
      final itemId = row['item_id'] as String?;
      final tagId = row['tag_id'] as String?;
      if (itemId == null || tagId == null) {
        failedRows += 1;
        logs.add(
          LegacyImportLogEntry.failed(
            table: 'item_tags',
            name: '$itemId/$tagId',
            reason: '标签关联信息不完整',
          ),
        );
        continue;
      }
      final existing = await _db.query(
        'item_tags',
        columns: ['item_id'],
        where: 'item_id = ? AND tag_id = ?',
        whereArgs: [itemId, tagId],
        limit: 1,
      );
      if (existing.isEmpty) {
        insertItemTags += 1;
      } else {
        skipItemTags += 1;
      }
    }

    return LegacyImportPreview(
      source: LegacyImportCounts(
        categories: categories.length,
        wikis: wikis.length,
        items: items.length,
        tags: tags.length,
        itemTags: itemTags.length,
      ),
      inserts: LegacyImportCounts(
        categories: insertCategories,
        wikis: insertWikis,
        items: insertItems,
        tags: insertTags,
        itemTags: insertItemTags,
      ),
      updates: LegacyImportCounts(
        categories: 0,
        wikis: updateWikis,
        items: updateItems,
        tags: 0,
        itemTags: 0,
      ),
      skipped: LegacyImportCounts(
        categories: skipCategories,
        wikis: skipWikis,
        items: skipItems,
        tags: skipTags,
        itemTags: skipItemTags,
      ),
      failedRows: failedRows,
      logs: logs,
    );
  }

  Future<int> clearDemoData() async {
    var deletedRows = 0;
    await _db.transaction((txn) async {
      for (final itemId in _demoItemIds) {
        deletedRows += await txn.delete(
          'items',
          where: 'id = ?',
          whereArgs: [itemId],
        );
      }
      for (final wikiId in _demoWikiIds) {
        final activeCount = Sqflite.firstIntValue(
              await txn.rawQuery(
                'SELECT COUNT(*) FROM items WHERE wiki_id = ?',
                [wikiId],
              ),
            ) ??
            0;
        if (activeCount == 0) {
          deletedRows += await txn.delete(
            'item_wikis',
            where: 'id = ?',
            whereArgs: [wikiId],
          );
        }
      }
    });
    return deletedRows;
  }

  Future<int> resetDemoData() async {
    final clearedRows = await clearDemoData();
    await _appDatabase.seedDemoData();
    return clearedRows;
  }

  Future<LegacyImportResult> importLegacyData(
    Map<String, dynamic> payload, {
    bool clearDemoBeforeImport = false,
  }) async {
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
    var updatedWikis = 0;
    var updatedItems = 0;
    var skippedCategories = 0;
    var skippedWikis = 0;
    var skippedItems = 0;
    var skippedTags = 0;
    var skippedItemTags = 0;
    var failedRows = 0;
    var clearedDemoRows = 0;
    final logs = <LegacyImportLogEntry>[];

    if (clearDemoBeforeImport) {
      clearedDemoRows = await clearDemoData();
      logs.add(
        LegacyImportLogEntry.updated(
          table: 'demo',
          name: '示例数据',
          reason: '导入前清理 $clearedDemoRows 条示例资料/库存',
        ),
      );
    }

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
          skippedCategories += 1;
          logs.add(
            LegacyImportLogEntry.skipped(
              table: 'categories',
              name: name,
              reason: '分类已存在，复用现有分类',
            ),
          );
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
          skippedCategories += 1;
          logs.add(
            LegacyImportLogEntry.skipped(
              table: 'categories',
              name: name,
              reason: '分类名称已存在，按名称合并',
            ),
          );
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
        logs.add(
          LegacyImportLogEntry.inserted(
            table: 'categories',
            name: name,
            reason: '新增旧版分类',
          ),
        );
      }

      final wikiIdMap = <String, String>{};
      for (final row in wikis) {
        final oldId = _requiredText(row['id'], fallback: _uuid.v4());
        final name = _requiredText(row['name'], fallback: '未命名物品');
        final categoryId = row['category_id'] == null
            ? null
            : categoryIdMap[row['category_id'] as String] ??
                row['category_id'] as String;
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
          columns: ['id', 'updated_at'],
          where: 'id = ?',
          whereArgs: [oldId],
          limit: 1,
        );
        if (existingById.isNotEmpty) {
          wikiIdMap[oldId] = oldId;
          if (_legacyRowIsNewer(row, existingById.first)) {
            await txn.update(
              'item_wikis',
              data,
              where: 'id = ?',
              whereArgs: [oldId],
            );
            updatedWikis += 1;
            logs.add(
              LegacyImportLogEntry.updated(
                table: 'wikis',
                name: name,
                reason: '更新较新的旧版物品资料',
              ),
            );
          } else {
            skippedWikis += 1;
            logs.add(
              LegacyImportLogEntry.skipped(
                table: 'wikis',
                name: name,
                reason: '物品资料已存在，现有资料更新或相同',
              ),
            );
          }
          continue;
        }

        final existingByName = await txn.query(
          'item_wikis',
          columns: ['id', 'updated_at'],
          where: 'lower(name) = lower(?)',
          whereArgs: [name],
          limit: 1,
        );
        if (existingByName.isNotEmpty) {
          final existingId = existingByName.first['id'] as String;
          wikiIdMap[oldId] = existingId;
          if (_legacyRowIsNewer(row, existingByName.first)) {
            await txn.update(
              'item_wikis',
              data,
              where: 'id = ?',
              whereArgs: [existingId],
            );
            updatedWikis += 1;
            logs.add(
              LegacyImportLogEntry.updated(
                table: 'wikis',
                name: name,
                reason: '按名称合并并更新较新的旧版物品资料',
              ),
            );
          } else {
            skippedWikis += 1;
            logs.add(
              LegacyImportLogEntry.skipped(
                table: 'wikis',
                name: name,
                reason: '物品资料名称已存在，现有资料更新或相同',
              ),
            );
          }
          continue;
        }

        await txn.insert('item_wikis', {
          'id': oldId,
          ...data,
          'created_at': _requiredText(row['created_at'], fallback: nowText),
        });
        wikiIdMap[oldId] = oldId;
        importedWikis += 1;
        logs.add(
          LegacyImportLogEntry.inserted(
            table: 'wikis',
            name: name,
            reason: '新增旧版物品资料',
          ),
        );
      }

      final itemIdMap = <String, String>{};
      for (final row in items) {
        final oldId = _requiredText(row['id'], fallback: _uuid.v4());
        final existingById = await txn.query(
          'items',
          columns: ['id', 'updated_at'],
          where: 'id = ?',
          whereArgs: [oldId],
          limit: 1,
        );

        final oldWikiId = row['wiki_id'] as String?;
        final wikiId =
            oldWikiId == null ? null : wikiIdMap[oldWikiId] ?? oldWikiId;
        if (wikiId == null) {
          failedRows += 1;
          logs.add(
            LegacyImportLogEntry.failed(
              table: 'items',
              name: _requiredText(row['name'], fallback: oldId),
              reason: '库存缺少可匹配的物品资料',
            ),
          );
          continue;
        }
        final wikiExists = await txn.query(
          'item_wikis',
          columns: ['id'],
          where: 'id = ?',
          whereArgs: [wikiId],
          limit: 1,
        );
        if (wikiExists.isEmpty) {
          failedRows += 1;
          logs.add(
            LegacyImportLogEntry.failed(
              table: 'items',
              name: _requiredText(row['name'], fallback: oldId),
              reason: '库存关联的物品资料不存在',
            ),
          );
          continue;
        }

        final data = _legacyItemData(
          row,
          wikiId: wikiId,
          nowText: nowText,
        );

        if (existingById.isNotEmpty) {
          if (_legacyRowIsNewer(row, existingById.first)) {
            await txn.update(
              'items',
              data,
              where: 'id = ?',
              whereArgs: [oldId],
            );
            updatedItems += 1;
            itemIdMap[oldId] = oldId;
            logs.add(
              LegacyImportLogEntry.updated(
                table: 'items',
                name: data['name']! as String,
                reason: '更新较新的旧版库存',
              ),
            );
          } else {
            skippedItems += 1;
            itemIdMap[oldId] = oldId;
            logs.add(
              LegacyImportLogEntry.skipped(
                table: 'items',
                name: data['name']! as String,
                reason: '库存已存在，现有资料更新或相同',
              ),
            );
          }
          continue;
        }

        final duplicate = await txn.query(
          'items',
          columns: ['id', 'updated_at'],
          where: '''
            lower(name) = lower(?)
            AND COALESCE(purchase_date, '') = COALESCE(?, '')
            AND COALESCE(expiry_date, '') = COALESCE(?, '')
          ''',
          whereArgs: [
            data['name'],
            data['purchase_date'] ?? '',
            data['expiry_date'] ?? '',
          ],
          limit: 1,
        );
        if (duplicate.isNotEmpty) {
          if (_legacyRowIsNewer(row, duplicate.first)) {
            final existingItemId = duplicate.first['id'] as String;
            await txn.update(
              'items',
              data,
              where: 'id = ?',
              whereArgs: [existingItemId],
            );
            updatedItems += 1;
            itemIdMap[oldId] = existingItemId;
            logs.add(
              LegacyImportLogEntry.updated(
                table: 'items',
                name: data['name']! as String,
                reason: '按名称/日期更新较新的旧版库存',
              ),
            );
          } else {
            skippedItems += 1;
            itemIdMap[oldId] = duplicate.first['id'] as String;
            logs.add(
              LegacyImportLogEntry.skipped(
                table: 'items',
                name: data['name']! as String,
                reason: '按名称/日期识别为重复库存',
              ),
            );
          }
          continue;
        }

        await txn.insert('items', {
          'id': oldId,
          ...data,
        });
        importedItems += 1;
        itemIdMap[oldId] = oldId;
        logs.add(
          LegacyImportLogEntry.inserted(
            table: 'items',
            name: data['name']! as String,
            reason: '新增旧版库存',
          ),
        );
      }

      final tagIdMap = <String, String>{};
      for (final row in tags) {
        final oldId = _requiredText(row['id'], fallback: _uuid.v4());
        final name = _blankToNull(row['name'] as String?);
        if (name == null) {
          failedRows += 1;
          logs.add(
            LegacyImportLogEntry.failed(
              table: 'tags',
              name: oldId,
              reason: '标签缺少名称',
            ),
          );
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
          skippedTags += 1;
          logs.add(
            LegacyImportLogEntry.skipped(
              table: 'tags',
              name: name,
              reason: '标签已存在',
            ),
          );
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
          skippedTags += 1;
          logs.add(
            LegacyImportLogEntry.skipped(
              table: 'tags',
              name: name,
              reason: '标签名称已存在',
            ),
          );
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
        logs.add(
          LegacyImportLogEntry.inserted(
            table: 'tags',
            name: name,
            reason: '新增旧版标签',
          ),
        );
      }

      for (final row in itemTags) {
        final oldItemId = row['item_id'] as String?;
        final oldTagId = row['tag_id'] as String?;
        if (oldItemId == null || oldTagId == null) {
          failedRows += 1;
          logs.add(
            LegacyImportLogEntry.failed(
              table: 'item_tags',
              name: '$oldItemId/$oldTagId',
              reason: '标签关联信息不完整',
            ),
          );
          continue;
        }
        final itemId = itemIdMap[oldItemId] ?? oldItemId;
        final tagId = tagIdMap[oldTagId] ?? oldTagId;
        final itemExists = await txn.query(
          'items',
          columns: ['id'],
          where: 'id = ?',
          whereArgs: [itemId],
          limit: 1,
        );
        final tagExists = await txn.query(
          'tags',
          columns: ['id'],
          where: 'id = ?',
          whereArgs: [tagId],
          limit: 1,
        );
        if (itemExists.isEmpty || tagExists.isEmpty) {
          failedRows += 1;
          logs.add(
            LegacyImportLogEntry.failed(
              table: 'item_tags',
              name: '$oldItemId/$oldTagId',
              reason: '标签关联指向的库存或标签不存在',
            ),
          );
          continue;
        }
        final existing = await txn.query(
          'item_tags',
          columns: ['item_id'],
          where: 'item_id = ? AND tag_id = ?',
          whereArgs: [itemId, tagId],
          limit: 1,
        );
        if (existing.isNotEmpty) {
          skippedItemTags += 1;
          continue;
        }
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

    final health = await checkDataHealth();
    final changedRows = importedCategories +
        importedWikis +
        importedItems +
        importedTags +
        importedItemTags +
        updatedWikis +
        updatedItems +
        clearedDemoRows;
    await _recordBackupRelevantChange(
      changedRows: changedRows,
      reason: '旧版库存导入',
      forceReminder: changedRows > 0,
    );
    return LegacyImportResult(
      categories: importedCategories,
      wikis: importedWikis,
      items: importedItems,
      tags: importedTags,
      itemTags: importedItemTags,
      updates: LegacyImportCounts(
        categories: 0,
        wikis: updatedWikis,
        items: updatedItems,
        tags: 0,
        itemTags: 0,
      ),
      skipped: LegacyImportCounts(
        categories: skippedCategories,
        wikis: skippedWikis,
        items: skippedItems,
        tags: skippedTags,
        itemTags: skippedItemTags,
      ),
      failedRows: failedRows,
      clearedDemoRows: clearedDemoRows,
      healthReport: health,
      logs: logs,
    );
  }

  Future<Map<String, Object?>?> _findExistingWikiForLegacyRow(
    Map<String, dynamic> row,
  ) async {
    final oldId = _requiredText(row['id'], fallback: _uuid.v4());
    final byId = await _db.query(
      'item_wikis',
      columns: ['id', 'updated_at'],
      where: 'id = ?',
      whereArgs: [oldId],
      limit: 1,
    );
    if (byId.isNotEmpty) {
      return byId.first;
    }

    final name = _requiredText(row['name'], fallback: '未命名物品');
    final byName = await _db.query(
      'item_wikis',
      columns: ['id', 'updated_at'],
      where: 'lower(name) = lower(?)',
      whereArgs: [name],
      limit: 1,
    );
    return byName.isEmpty ? null : byName.first;
  }

  Future<bool> _wikiExists(String wikiId) async {
    final rows = await _db.query(
      'item_wikis',
      columns: ['id'],
      where: 'id = ?',
      whereArgs: [wikiId],
      limit: 1,
    );
    return rows.isNotEmpty;
  }

  Future<Map<String, Object?>?> _findExistingItemForLegacyRow(
    Map<String, dynamic> row,
  ) async {
    final oldId = _requiredText(row['id'], fallback: _uuid.v4());
    final byId = await _db.query(
      'items',
      columns: ['id', 'updated_at'],
      where: 'id = ?',
      whereArgs: [oldId],
      limit: 1,
    );
    if (byId.isNotEmpty) {
      return byId.first;
    }

    final name = _requiredText(row['name'], fallback: '未命名物品');
    final byNameAndDate = await _db.query(
      'items',
      columns: ['id', 'updated_at'],
      where: '''
        lower(name) = lower(?)
        AND COALESCE(purchase_date, '') = COALESCE(?, '')
        AND COALESCE(expiry_date, '') = COALESCE(?, '')
      ''',
      whereArgs: [
        name,
        _dateTextFromPayload(row['purchase_date']) ?? '',
        _dateTextFromPayload(row['expiry_date']) ?? '',
      ],
      limit: 1,
    );
    return byNameAndDate.isEmpty ? null : byNameAndDate.first;
  }

  bool _legacyRowIsNewer(
    Map<String, dynamic> incoming,
    Map<String, Object?> existing,
  ) {
    final incomingText = _dateTimeTextFromPayload(incoming['updated_at']);
    final existingText = existing['updated_at'] as String?;
    if (incomingText == null || existingText == null) {
      return false;
    }
    final incomingDate = DateTime.tryParse(incomingText);
    final existingDate = DateTime.tryParse(existingText);
    if (incomingDate == null || existingDate == null) {
      return false;
    }
    return incomingDate.isAfter(existingDate);
  }

  Map<String, Object?> _legacyItemData(
    Map<String, dynamic> row, {
    required String wikiId,
    required String nowText,
  }) {
    return {
      'wiki_id': wikiId,
      'name': _requiredText(row['name'], fallback: '未命名物品'),
      'description': _blankToNull(row['description'] as String?),
      'quantity': _positiveIntValue(row['quantity'], fallback: 1),
      'unit': _blankToNull(row['unit'] as String?),
      'purchase_date': _dateTextFromPayload(row['purchase_date']),
      'expiry_date': _dateTextFromPayload(row['expiry_date']),
      'reminder_date': _dateTextFromPayload(row['reminder_date']),
      'status': ItemStatus.fromDbValue(row['status'] as String?).dbValue,
      'is_reminder_enabled': _boolAsInt(row['is_reminder_enabled']),
      'reminder_days_before':
          _positiveIntValue(row['reminder_days_before'], fallback: 3),
      'consumed_at': _dateTimeTextFromPayload(row['consumed_at']),
      'predicted_expiry_date':
          _dateTextFromPayload(row['predicted_expiry_date']),
      'prediction_confidence': _confidenceValue(row['prediction_confidence']),
      'recognition_confidence': _confidenceValue(row['recognition_confidence']),
      'image_path': _blankToNull(row['image_path'] as String?),
      'storage_location': _blankToNull(row['storage_location'] as String?),
      'source_app': _blankToNull(row['source_app'] as String?),
      'source_order_id': _blankToNull(row['source_order_id'] as String?),
      'import_batch_id': _blankToNull(row['import_batch_id'] as String?),
      'created_at': _dateTimeTextFromPayload(row['created_at']) ?? nowText,
      'updated_at': _dateTimeTextFromPayload(row['updated_at']) ?? nowText,
    };
  }

  Future<Map<String, dynamic>> exportBackup() async {
    final data = <String, List<Map<String, Object?>>>{};
    for (final table in _backupTables) {
      data[table] = await _db.query(table);
    }
    return {
      'schema_version': AppDatabase.schemaVersion,
      'exported_at': DateTime.now().toIso8601String(),
      'data': data,
    };
  }

  Future<String> exportInventoryCsv() async {
    final rows = await _db.rawQuery('''
      SELECT
        i.*,
        w.icon AS wiki_icon,
        c.name AS category_name,
        (
          SELECT GROUP_CONCAT(t.name, '||')
          FROM item_tags it
          JOIN tags t ON t.id = it.tag_id
          WHERE it.item_id = i.id
        ) AS tag_names
      FROM items i
      LEFT JOIN item_wikis w ON w.id = i.wiki_id
      LEFT JOIN item_wiki_categories c ON c.id = w.category_id
      ORDER BY i.name COLLATE NOCASE ASC, i.created_at DESC
    ''');
    final items = rows.map(InventoryItem.fromMap).toList();
    final buffer = StringBuffer();
    buffer.write('\ufeff');
    buffer.writeln(
      _csvRow([
        '物品名称',
        '分类',
        '状态',
        '数量',
        '单位',
        '购买日期',
        '过期日期',
        '存放位置',
        '标签',
        '来源',
      ]),
    );
    for (final item in items) {
      buffer.writeln(
        _csvRow([
          item.name,
          item.categoryName ?? '',
          item.status.label,
          '${item.quantity}',
          item.unit ?? '',
          _csvDate(item.purchaseDate),
          _csvDate(item.expiryDate),
          item.storageLocation ?? '',
          item.tags.join(';'),
          item.sourceApp ?? '',
        ]),
      );
    }
    return buffer.toString();
  }

  Future<BackupSnapshot> createBackupSnapshot({String? label}) async {
    final backup = await exportBackup();
    final snapshot = BackupSnapshot(
      id: _uuid.v4(),
      createdAt: DateTime.now(),
      schemaVersion: AppDatabase.schemaVersion,
      label: _blankToNull(label),
      payloadJson: jsonEncode(backup),
    );
    await _db.insert('backup_snapshots', snapshot.toMap());
    return snapshot;
  }

  Future<List<BackupSnapshot>> getBackupSnapshots() async {
    final rows = await _db.query(
      'backup_snapshots',
      orderBy: 'created_at DESC',
    );
    return rows.map(BackupSnapshot.fromMap).toList();
  }

  Future<BackupReminderState> getBackupReminderState() async {
    final metadata = await _getAppMetadata([
      _metadataBackupReminderPending,
      _metadataBackupReminderReason,
      _metadataBackupDirtyCount,
      _metadataBackupReminderUpdatedAt,
      _metadataLastBackupExportedAt,
    ]);
    final pending = metadata[_metadataBackupReminderPending] == '1';
    final dirtyCount =
        int.tryParse(metadata[_metadataBackupDirtyCount] ?? '0') ?? 0;
    return BackupReminderState(
      isPending: pending,
      reason: metadata[_metadataBackupReminderReason],
      dirtyCount: dirtyCount,
      updatedAt: _dateTimeFromPayload(
        metadata[_metadataBackupReminderUpdatedAt],
      ),
      lastExportedAt: _dateTimeFromPayload(
        metadata[_metadataLastBackupExportedAt],
      ),
    );
  }

  Future<void> markBackupExported({DateTime? exportedAt}) async {
    final now = exportedAt ?? DateTime.now();
    await _setAppMetadata({
      _metadataLastBackupExportedAt: now.toIso8601String(),
      _metadataBackupReminderPending: '0',
      _metadataBackupReminderReason: '',
      _metadataBackupDirtyCount: '0',
      _metadataBackupReminderUpdatedAt: now.toIso8601String(),
    });
  }

  Future<BackupRestoreResult> restoreBackup(
    Map<String, dynamic> backup, {
    bool replaceExisting = false,
  }) async {
    final data = backup['data'];
    if (data is! Map) {
      throw ArgumentError('备份数据格式不正确');
    }
    final backupRows = _normalizeBackupData(data);

    final before = await createBackupSnapshot(label: '恢复前自动备份');
    var restoredRows = 0;
    await _db.transaction((txn) async {
      if (replaceExisting) {
        for (final table in _backupTables.reversed) {
          await txn.delete(table);
        }
      }

      for (final table in _backupTables) {
        final rows = backupRows[table]!;
        for (final row in rows) {
          await txn.insert(
            table,
            row,
            conflictAlgorithm: ConflictAlgorithm.replace,
          );
          restoredRows += 1;
        }
      }

      final health = await _checkDataHealth(txn);
      if (!health.passed) {
        throw StateError('恢复后的资料检查未通过：${health.summary}');
      }
    });

    return BackupRestoreResult(
      restoredRows: restoredRows,
      preRestoreSnapshotId: before.id,
    );
  }

  Map<String, List<Map<String, Object?>>> _normalizeBackupData(Map data) {
    final normalized = <String, List<Map<String, Object?>>>{};
    for (final table in _backupTables) {
      if (!data.containsKey(table)) {
        throw const FormatException('备份文件内容不完整或已损坏');
      }
      final rows = data[table];
      if (rows is! List) {
        throw const FormatException('备份文件内容不完整或已损坏');
      }
      normalized[table] = rows.map((row) {
        if (row is! Map) {
          throw const FormatException('备份文件内容不完整或已损坏');
        }
        try {
          return Map<String, Object?>.from(row);
        } catch (_) {
          throw const FormatException('备份文件内容不完整或已损坏');
        }
      }).toList();
    }
    return normalized;
  }

  Future<DataHealthReport> checkDataHealth() async {
    return _checkDataHealth(_db);
  }

  Future<DataHealthReport> _checkDataHealth(DatabaseExecutor executor) async {
    final issues = <DataHealthIssue>[];

    await _addCountIssue(
      executor,
      issues,
      code: 'non_positive_quantity',
      message: '库存数量必须大于 0',
      query: 'SELECT COUNT(*) FROM items WHERE quantity <= 0',
    );
    await _addCountIssue(
      executor,
      issues,
      code: 'invalid_status',
      message: '库存状态需要修正',
      query: '''
        SELECT COUNT(*)
        FROM items
        WHERE status NOT IN ('active', 'expired', 'consumed', 'wasted')
      ''',
    );
    await _addCountIssue(
      executor,
      issues,
      code: 'negative_reminder_days',
      message: '提醒提前天数不能小于 0',
      query: '''
        SELECT COUNT(*)
        FROM items
        WHERE reminder_days_before < 0
      ''',
    );
    await _addCountIssue(
      executor,
      issues,
      code: 'negative_default_reminder_days',
      message: '物品资料默认提醒提前天数不能小于 0',
      query: '''
        SELECT COUNT(*)
        FROM item_wikis
        WHERE default_reminder_days < 0
      ''',
    );
    await _addCountIssue(
      executor,
      issues,
      code: 'orphan_item',
      message: '库存记录缺少对应物品资料',
      query: '''
        SELECT COUNT(*)
        FROM items i
        LEFT JOIN item_wikis w ON w.id = i.wiki_id
        WHERE w.id IS NULL
      ''',
    );
    await _addCountIssue(
      executor,
      issues,
      code: 'active_with_consumed_at',
      message: '使用中库存不应带有消耗时间',
      query: '''
        SELECT COUNT(*)
        FROM items
        WHERE status = 'active' AND consumed_at IS NOT NULL
      ''',
    );
    await _addCountIssue(
      executor,
      issues,
      code: 'consumed_without_consumed_at',
      message: '已消耗库存缺少消耗时间',
      query: '''
        SELECT COUNT(*)
        FROM items
        WHERE status = 'consumed' AND consumed_at IS NULL
      ''',
    );
    await _addCountIssue(
      executor,
      issues,
      code: 'reminder_after_expiry',
      message: '提醒日期不能晚于过期日期',
      query: '''
        SELECT COUNT(*)
        FROM items
        WHERE reminder_date IS NOT NULL
          AND expiry_date IS NOT NULL
          AND reminder_date > expiry_date
      ''',
    );
    await _addCountIssue(
      executor,
      issues,
      code: 'orphan_item_tag',
      message: '标签关联缺少对应库存或标签',
      query: '''
        SELECT COUNT(*)
        FROM item_tags it
        LEFT JOIN items i ON i.id = it.item_id
        LEFT JOIN tags t ON t.id = it.tag_id
        WHERE i.id IS NULL OR t.id IS NULL
      ''',
    );
    await _addCountIssue(
      executor,
      issues,
      code: 'non_positive_shopping_quantity',
      message: '采购清单数量必须大于 0',
      query: 'SELECT COUNT(*) FROM shopping_list_items WHERE quantity <= 0',
    );
    await _addCountIssue(
      executor,
      issues,
      code: 'invalid_shopping_checked_state',
      message: '采购清单勾选状态不在允许集合内',
      query: '''
        SELECT COUNT(*)
        FROM shopping_list_items
        WHERE is_checked NOT IN (0, 1)
      ''',
    );

    final foreignKeyRows = await executor.rawQuery('PRAGMA foreign_key_check');
    if (foreignKeyRows.isNotEmpty) {
      issues.add(
        DataHealthIssue(
          code: 'foreign_key_violation',
          message: '资料关联需要修正',
          count: foreignKeyRows.length,
        ),
      );
    }

    final dateRows = await executor.query(
      'items',
      columns: [
        'purchase_date',
        'expiry_date',
        'reminder_date',
        'consumed_at',
        'predicted_expiry_date',
        'created_at',
        'updated_at',
      ],
    );
    final shoppingDateRows = await executor.query(
      'shopping_list_items',
      columns: [
        'checked_at',
        'converted_at',
        'created_at',
        'updated_at',
      ],
    );
    var invalidDateCount = 0;
    for (final row in [...dateRows, ...shoppingDateRows]) {
      for (final value in row.values) {
        if (value is String && value.trim().isNotEmpty) {
          if (DateTime.tryParse(value) == null) {
            invalidDateCount += 1;
          }
        }
      }
    }
    if (invalidDateCount > 0) {
      issues.add(
        DataHealthIssue(
          code: 'invalid_date',
          message: '日期格式不正确',
          count: invalidDateCount,
        ),
      );
    }

    return DataHealthReport(issues: issues);
  }

  Future<void> _addCountIssue(
    DatabaseExecutor executor,
    List<DataHealthIssue> issues, {
    required String code,
    required String message,
    required String query,
  }) async {
    final count = Sqflite.firstIntValue(await executor.rawQuery(query)) ?? 0;
    if (count > 0) {
      issues.add(
        DataHealthIssue(
          code: code,
          message: message,
          count: count,
        ),
      );
    }
  }

  Future<void> _recordBackupRelevantChange({
    required int changedRows,
    required String reason,
    bool forceReminder = false,
  }) async {
    if (changedRows <= 0) {
      return;
    }
    final metadata = await _getAppMetadata([
      _metadataBackupDirtyCount,
      _metadataBackupReminderPending,
    ]);
    final currentDirtyCount =
        int.tryParse(metadata[_metadataBackupDirtyCount] ?? '0') ?? 0;
    final nextDirtyCount = currentDirtyCount + changedRows;
    final shouldPrompt = forceReminder ||
        metadata[_metadataBackupReminderPending] == '1' ||
        nextDirtyCount >= _backupReminderDirtyThreshold;
    final nowText = DateTime.now().toIso8601String();
    await _setAppMetadata({
      _metadataBackupDirtyCount: '$nextDirtyCount',
      _metadataBackupReminderUpdatedAt: nowText,
      if (shouldPrompt) _metadataBackupReminderPending: '1',
      if (shouldPrompt) _metadataBackupReminderReason: reason,
    });
  }

  Future<Map<String, String>> _getAppMetadata(List<String> keys) async {
    if (keys.isEmpty) {
      return const {};
    }
    final placeholders = List.filled(keys.length, '?').join(', ');
    final rows = await _db.query(
      'app_metadata',
      columns: ['key', 'value'],
      where: 'key IN ($placeholders)',
      whereArgs: keys,
    );
    return {
      for (final row in rows) row['key'] as String: row['value'] as String,
    };
  }

  Future<void> _setAppMetadata(Map<String, String> values) async {
    if (values.isEmpty) {
      return;
    }
    final nowText = DateTime.now().toIso8601String();
    await _db.transaction((txn) async {
      for (final entry in values.entries) {
        await txn.insert(
          'app_metadata',
          {
            'key': entry.key,
            'value': entry.value,
            'updated_at': nowText,
          },
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
    });
  }
}

const _backupTables = [
  'item_wiki_categories',
  'item_wikis',
  'items',
  'tags',
  'item_tags',
  'reminder_logs',
  'shopping_list_items',
  'app_metadata',
];

const _reminderActionIgnored = 'ignored';
const _reminderActionSnoozed = 'snoozed';
const _backupReminderDirtyThreshold = 10;
const _metadataBackupReminderPending = 'backup_reminder_pending';
const _metadataBackupReminderReason = 'backup_reminder_reason';
const _metadataBackupDirtyCount = 'backup_dirty_count';
const _metadataBackupReminderUpdatedAt = 'backup_reminder_updated_at';
const _metadataLastBackupExportedAt = 'last_backup_exported_at';

const _demoWikiIds = [
  'wiki-milk',
  'wiki-egg',
  'wiki-bread',
  'wiki-toothpaste',
  'wiki-cold-medicine',
];

const _demoItemIds = [
  'item-milk-1',
  'item-egg-1',
  'item-bread-1',
  'item-cold-medicine-1',
];

class LegacyImportCounts {
  const LegacyImportCounts({
    this.categories = 0,
    this.wikis = 0,
    this.items = 0,
    this.tags = 0,
    this.itemTags = 0,
  });

  final int categories;
  final int wikis;
  final int items;
  final int tags;
  final int itemTags;

  int get total => categories + wikis + items + tags + itemTags;
}

class LegacyImportPreview {
  const LegacyImportPreview({
    required this.source,
    required this.inserts,
    required this.updates,
    required this.skipped,
    required this.failedRows,
    required this.logs,
  });

  final LegacyImportCounts source;
  final LegacyImportCounts inserts;
  final LegacyImportCounts updates;
  final LegacyImportCounts skipped;
  final int failedRows;
  final List<LegacyImportLogEntry> logs;

  int get writableRows => inserts.total + updates.total;
  bool get hasImportableRows => writableRows > 0;
  bool get hasWarnings => skipped.total > 0 || failedRows > 0;
}

class LegacyImportLogEntry {
  const LegacyImportLogEntry({
    required this.table,
    required this.name,
    required this.action,
    required this.reason,
  });

  factory LegacyImportLogEntry.inserted({
    required String table,
    required String name,
    required String reason,
  }) {
    return LegacyImportLogEntry(
      table: table,
      name: name,
      action: 'inserted',
      reason: reason,
    );
  }

  factory LegacyImportLogEntry.updated({
    required String table,
    required String name,
    required String reason,
  }) {
    return LegacyImportLogEntry(
      table: table,
      name: name,
      action: 'updated',
      reason: reason,
    );
  }

  factory LegacyImportLogEntry.skipped({
    required String table,
    required String name,
    required String reason,
  }) {
    return LegacyImportLogEntry(
      table: table,
      name: name,
      action: 'skipped',
      reason: reason,
    );
  }

  factory LegacyImportLogEntry.failed({
    required String table,
    required String name,
    required String reason,
  }) {
    return LegacyImportLogEntry(
      table: table,
      name: name,
      action: 'failed',
      reason: reason,
    );
  }

  final String table;
  final String name;
  final String action;
  final String reason;
}

class LegacyImportResult {
  const LegacyImportResult({
    required this.categories,
    required this.wikis,
    required this.items,
    required this.tags,
    required this.itemTags,
    this.updates = const LegacyImportCounts(),
    this.skipped = const LegacyImportCounts(),
    this.failedRows = 0,
    this.clearedDemoRows = 0,
    this.healthReport,
    this.logs = const [],
  });

  final int categories;
  final int wikis;
  final int items;
  final int tags;
  final int itemTags;
  final LegacyImportCounts updates;
  final LegacyImportCounts skipped;
  final int failedRows;
  final int clearedDemoRows;
  final DataHealthReport? healthReport;
  final List<LegacyImportLogEntry> logs;

  int get total => categories + wikis + items + tags + itemTags;
  bool get healthPassed => healthReport?.passed ?? false;
}

class BackupSnapshot {
  const BackupSnapshot({
    required this.id,
    required this.createdAt,
    required this.schemaVersion,
    required this.payloadJson,
    this.label,
  });

  final String id;
  final DateTime createdAt;
  final int schemaVersion;
  final String? label;
  final String payloadJson;

  factory BackupSnapshot.fromMap(Map<String, Object?> map) {
    return BackupSnapshot(
      id: map['id'] as String,
      createdAt: DateTime.parse(map['created_at'] as String),
      schemaVersion: (map['schema_version'] as int?) ?? 1,
      label: map['label'] as String?,
      payloadJson: map['payload_json'] as String,
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'created_at': createdAt.toIso8601String(),
      'schema_version': schemaVersion,
      'label': label,
      'payload_json': payloadJson,
    };
  }
}

class BackupReminderState {
  const BackupReminderState({
    required this.isPending,
    this.reason,
    this.dirtyCount = 0,
    this.updatedAt,
    this.lastExportedAt,
  });

  static const none = BackupReminderState(isPending: false);

  final bool isPending;
  final String? reason;
  final int dirtyCount;
  final DateTime? updatedAt;
  final DateTime? lastExportedAt;

  String get message {
    if (!isPending) {
      return '当前没有待处理的备份提醒';
    }
    if (reason == null || reason!.isEmpty) {
      return '库存资料有更新，建议备份一次';
    }
    return '因为$reason，建议备份一次';
  }
}

class PendingReminderNotification {
  const PendingReminderNotification({
    required this.itemId,
    required this.title,
    required this.body,
    required this.scheduledAt,
  });

  final String itemId;
  final String title;
  final String body;
  final DateTime scheduledAt;

  factory PendingReminderNotification.fromItem(
    InventoryItem item,
    DateTime now,
  ) {
    final dueDate = item.reminderDate ?? item.expiryDate ?? now;
    final scheduledDate = DateTime(
      dueDate.year,
      dueDate.month,
      dueDate.day,
      9,
    );
    final earliest = now.add(const Duration(minutes: 1));
    final effectiveSchedule =
        scheduledDate.isBefore(earliest) ? earliest : scheduledDate;
    final days = item.daysUntilExpiry;
    final title = days == null
        ? '${item.name} 需要处理'
        : days < 0
            ? '${item.name} 已过期'
            : days == 0
                ? '${item.name} 今天到期'
                : '${item.name} $days 天后到期';
    final quantity = '${item.quantity}${item.unit ?? ''}';
    final location = item.storageLocation ?? item.categoryName ?? '库存';
    return PendingReminderNotification(
      itemId: item.id,
      title: title,
      body: '$quantity · $location · 打开查看详情',
      scheduledAt: effectiveSchedule,
    );
  }

  Map<String, Object?> toMap() {
    return {
      'itemId': itemId,
      'title': title,
      'body': body,
      'scheduledAtMillis': scheduledAt.millisecondsSinceEpoch,
    };
  }
}

class BackupRestoreResult {
  const BackupRestoreResult({
    required this.restoredRows,
    required this.preRestoreSnapshotId,
  });

  final int restoredRows;
  final String preRestoreSnapshotId;
}

class DataHealthReport {
  const DataHealthReport({required this.issues});

  final List<DataHealthIssue> issues;

  bool get passed => issues.isEmpty;

  String get summary {
    if (passed) {
      return '资料检查正常';
    }
    return issues.map((issue) => '${issue.message} ${issue.count} 处').join('；');
  }
}

class DataHealthIssue {
  const DataHealthIssue({
    required this.code,
    required this.message,
    required this.count,
  });

  final String code;
  final String message;
  final int count;
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

List<String> _normalizeItemIds(Iterable<String> itemIds) {
  final ids = <String>[];
  final seen = <String>{};
  for (final itemId in itemIds) {
    final normalized = itemId.trim();
    if (normalized.isEmpty || seen.contains(normalized)) {
      continue;
    }
    seen.add(normalized);
    ids.add(normalized);
  }
  return ids;
}

String _csvRow(List<String> cells) {
  return cells.map(_csvCell).join(',');
}

String _csvCell(String value) {
  final escaped = value.replaceAll('"', '""');
  if (escaped.contains(',') ||
      escaped.contains('\n') ||
      escaped.contains('\r') ||
      escaped.contains('"')) {
    return '"$escaped"';
  }
  return escaped;
}

String _csvDate(DateTime? value) {
  if (value == null) {
    return '';
  }
  final year = value.year.toString().padLeft(4, '0');
  final month = value.month.toString().padLeft(2, '0');
  final day = value.day.toString().padLeft(2, '0');
  return '$year-$month-$day';
}

List<Map<String, dynamic>> _payloadList(Object? value) {
  if (value is! List) {
    return [];
  }
  return value
      .whereType<Map>()
      .map((row) => Map<String, dynamic>.from(row))
      .toList();
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

int _positiveIntValue(Object? value, {required int fallback}) {
  final parsed = _intValue(value, fallback: fallback);
  return parsed > 0 ? parsed : fallback;
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

double? _confidenceValue(Object? value) {
  final number = value is num ? value.toDouble() : null;
  if (number == null || number < 0 || number > 1) {
    return null;
  }
  return number;
}

String? _dateTextFromPayload(Object? value) {
  final text = _blankToNull(value is String ? value : null);
  if (text == null) {
    return null;
  }
  final parsed = DateTime.tryParse(text);
  return parsed == null ? null : _dateText(parsed);
}

String? _dateTimeTextFromPayload(Object? value) {
  final text = _blankToNull(value is String ? value : null);
  if (text == null) {
    return null;
  }
  final parsed = DateTime.tryParse(text);
  return parsed?.toIso8601String();
}

DateTime? _dateTimeFromPayload(Object? value) {
  final text = _blankToNull(value is String ? value : null);
  if (text == null) {
    return null;
  }
  return DateTime.tryParse(text);
}

void _validateInventoryDraft({
  required int quantity,
  DateTime? purchaseDate,
  DateTime? expiryDate,
  int? reminderDaysBefore,
  double? predictionConfidence,
  double? recognitionConfidence,
}) {
  if (quantity <= 0) {
    throw ArgumentError('数量必须大于 0');
  }
  if (reminderDaysBefore != null && reminderDaysBefore < 0) {
    throw ArgumentError('提醒提前天数不能小于 0');
  }
  if (purchaseDate != null &&
      expiryDate != null &&
      _dateOnly(purchaseDate).isAfter(_dateOnly(expiryDate))) {
    throw ArgumentError('购买日期不能晚于过期日期');
  }
  if (predictionConfidence != null &&
      (predictionConfidence < 0 || predictionConfidence > 1)) {
    throw ArgumentError('预测置信度必须在 0 到 1 之间');
  }
  if (recognitionConfidence != null &&
      (recognitionConfidence < 0 || recognitionConfidence > 1)) {
    throw ArgumentError('识别置信度必须在 0 到 1 之间');
  }
}
