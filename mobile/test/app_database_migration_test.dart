import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/app_database.dart';
import 'package:vibe_fridge/data/inventory_repository.dart';

import 'test_database.dart';

void main() {
  test('migrates v1 database to latest schema without data loss', () async {
    final appDatabase = await openTestDatabase(version: 1);
    addTearDown(() => appDatabase.database.close());
    final db = appDatabase.database;
    const now = '2026-06-15T00:00:00.000';

    await db.insert('item_wiki_categories', {
      'id': 'cat-test',
      'name': '测试分类',
      'icon': 'category',
      'color': '#000000',
      'sort_order': 1,
      'created_at': now,
      'updated_at': now,
    });
    await db.insert('item_wikis', {
      'id': 'wiki-test',
      'name': '迁移测试物品',
      'icon': null,
      'description': null,
      'category_id': 'cat-test',
      'default_unit': '个',
      'suggested_expiry_days': 7,
      'storage_location': '冷藏',
      'notes': null,
      'image_path': null,
      'created_at': now,
      'updated_at': now,
    });
    await db.insert('items', {
      'id': 'item-test',
      'wiki_id': 'wiki-test',
      'name': '迁移测试物品',
      'description': null,
      'quantity': 2,
      'unit': '个',
      'purchase_date': '2026-06-15T00:00:00.000',
      'expiry_date': '2026-06-22T00:00:00.000',
      'reminder_date': '2026-06-19T00:00:00.000',
      'status': 'active',
      'is_reminder_enabled': 1,
      'consumed_at': null,
      'predicted_expiry_date': null,
      'prediction_confidence': null,
      'image_path': null,
      'source_app': null,
      'source_order_id': null,
      'created_at': now,
      'updated_at': now,
    });

    await AppDatabase.migrateSchemaForTesting(
      db,
      1,
      AppDatabase.schemaVersion,
    );

    final repository = InventoryRepository(appDatabase);
    final item = await repository.getItem('item-test');
    expect(item?.name, '迁移测试物品');
    expect(item?.quantity, 2);

    final itemColumns = await db.rawQuery('PRAGMA table_info(items)');
    expect(
      itemColumns.map((row) => row['name']),
      containsAll([
        'storage_location',
        'reminder_days_before',
        'import_batch_id',
        'recognition_confidence',
      ]),
    );

    final wikiColumns = await db.rawQuery('PRAGMA table_info(item_wikis)');
    expect(
      wikiColumns.map((row) => row['name']),
      contains('default_reminder_days'),
    );

    final shoppingColumns = await db.rawQuery(
      'PRAGMA table_info(shopping_list_items)',
    );
    expect(
      shoppingColumns.map((row) => row['name']),
      containsAll([
        'name',
        'quantity',
        'is_checked',
        'converted_at',
      ]),
    );

    final itemIndexes = await db.rawQuery('PRAGMA index_list(items)');
    expect(
      itemIndexes.map((row) => row['name']),
      containsAll([
        'idx_items_status_expiry',
        'idx_items_status_reminder',
        'idx_items_wiki_status',
      ]),
    );

    final reminderIndexes =
        await db.rawQuery('PRAGMA index_list(reminder_logs)');
    expect(
      reminderIndexes.map((row) => row['name']),
      contains('idx_reminder_logs_item_type_sent'),
    );

    final snapshot = await repository.createBackupSnapshot(label: '迁移测试');
    expect(snapshot.schemaVersion, AppDatabase.schemaVersion);

    final health = await repository.checkDataHealth();
    expect(health.passed, isTrue);
  });
}
