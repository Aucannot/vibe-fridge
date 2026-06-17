import 'dart:convert';

import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/acceptance_test_service.dart';
import 'package:vibe_fridge/data/app_database.dart';
import 'package:vibe_fridge/data/inventory_controller.dart';
import 'package:vibe_fridge/data/inventory_repository.dart';
import 'package:vibe_fridge/models/item_status.dart';
import 'package:vibe_fridge/models/order_recognition.dart';
import 'package:vibe_fridge/models/shopping_list_item.dart';

import 'test_database.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AppDatabase appDatabase;
  late InventoryRepository repository;

  setUp(() async {
    appDatabase = await openTestDatabase();
    repository = InventoryRepository(appDatabase);
    await repository.seedDefaults();
  });

  tearDown(() async {
    await appDatabase.database.close();
  });

  test('resets demo data without deleting user inventory', () async {
    const userName = '用户自建重置保护苹果';
    final categories = await repository.getCategories();
    await repository.createItem(
      name: userName,
      categoryId: categories.first.id,
      quantity: 3,
      unit: '个',
      purchaseDate: DateTime(2026, 6, 1),
      expiryDate: DateTime(2026, 6, 8),
    );

    final clearedRows = await repository.resetDemoData();
    expect(clearedRows, greaterThan(0));

    final demo = await repository.getRegisteredItems(keyword: '鲜牛奶');
    expect(demo, isNotEmpty);
    expect(demo.single.totalQuantity, 2);

    final userItems = await repository.getRegisteredItems(keyword: userName);
    expect(userItems, hasLength(1));
    expect(userItems.single.totalQuantity, 3);
  });

  test('completes create update consume restore and delete loop', () async {
    const name = '闭环测试酸奶';
    final categories = await repository.getCategories();
    final purchaseDate = DateTime.now();
    final expiryDate = purchaseDate.add(const Duration(days: 7));
    final reminderDate = DateTime(
      expiryDate.year,
      expiryDate.month,
      expiryDate.day,
    ).subtract(const Duration(days: 3));

    await repository.createItem(
      name: name,
      categoryId: categories.first.id,
      quantity: 2,
      unit: '盒',
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
      imagePath: '/tmp/vibe-fridge/package.jpg',
      storageLocation: '冷藏',
      tags: const ['临期优先', '已开封'],
    );

    final registered = await repository.getRegisteredItems(keyword: name);
    expect(registered, hasLength(1));
    expect(registered.single.activeBatchCount, 1);
    expect(registered.single.totalQuantity, 2);

    final wikiId = registered.single.wikiId;
    final items = await repository.getInventoryByWikiId(wikiId);
    expect(items, hasLength(1));
    expect(items.single.quantity, 2);
    expect(items.single.reminderDate, reminderDate);
    expect(items.single.reminderDaysBefore, 3);
    expect(items.single.imagePath, '/tmp/vibe-fridge/package.jpg');
    expect(items.single.storageLocation, '冷藏');
    expect(items.single.tags, containsAll(['临期优先', '已开封']));

    await repository.updateItemQuantity(items.single.id, 1);
    final updated = await repository.getItem(items.single.id);
    expect(updated?.quantity, 3);

    await repository.updateItem(
      itemId: items.single.id,
      quantity: 3,
      unit: '盒',
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
      imagePath: '/tmp/vibe-fridge/package-new.jpg',
      storageLocation: '冷冻',
      tags: const ['囤货'],
    );
    final moved = await repository.getItem(items.single.id);
    expect(moved?.imagePath, '/tmp/vibe-fridge/package-new.jpg');
    expect(moved?.storageLocation, '冷冻');
    expect(moved?.tags, ['囤货']);

    await repository.markAsConsumed(items.single.id);
    final remaining = await repository.getItem(items.single.id);
    expect(remaining?.status, ItemStatus.active);
    expect(remaining?.quantity, 2);

    final consumed = (await repository.getHistoryItems())
        .singleWhere((item) => item.name == name);
    expect(consumed.status, ItemStatus.consumed);
    expect(consumed.quantity, 1);

    await repository.restoreItem(consumed.id);
    final restored = await repository.getItem(consumed.id);
    expect(restored?.status, ItemStatus.active);

    await repository.deleteItem(consumed.id);
    expect(await repository.getItem(consumed.id), isNull);

    await repository.deleteItem(items.single.id);
    await repository.deleteWiki(wikiId, force: true);
    expect(await repository.getWiki(wikiId), isNull);
  });

  test('keeps same-name same-expiry inventory as separate batches', () async {
    const name = '批次策略测试鸡蛋';
    final categories = await repository.getCategories();
    final purchaseDate = DateTime(2026, 6, 1);
    final expiryDate = DateTime(2026, 6, 8);

    await repository.createItem(
      name: name,
      categoryId: categories.first.id,
      quantity: 6,
      unit: '个',
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
    );
    await repository.createItem(
      name: name,
      categoryId: categories.first.id,
      quantity: 4,
      unit: '个',
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
    );

    final registered = (await repository.getRegisteredItems(keyword: name))
        .singleWhere((item) => item.name == name);
    expect(registered.activeBatchCount, 2);
    expect(registered.totalQuantity, 10);

    final batches = await repository.getInventoryByWikiId(registered.wikiId);
    expect(batches, hasLength(2));
    expect(batches.map((item) => item.quantity), containsAll([6, 4]));
    expect(batches.map((item) => item.expiryDate).toSet(), {expiryDate});
  });

  test('performs batch inventory actions', () async {
    final categories = await repository.getCategories();
    final foodCategory = categories.firstWhere(
      (category) => category.name == '食品',
    );
    final dailyCategory = categories.firstWhere(
      (category) => category.name == '日用品',
    );

    await repository.createItem(
      name: '批量操作测试牛奶',
      categoryId: foodCategory.id,
      quantity: 2,
      unit: '盒',
      storageLocation: '冷藏',
    );
    await repository.createItem(
      name: '批量操作测试纸巾',
      categoryId: foodCategory.id,
      quantity: 1,
      unit: '包',
      storageLocation: '常温',
    );

    final milkWiki = (await repository.getRegisteredItems(
      keyword: '批量操作测试牛奶',
    ))
        .single;
    final tissueWiki = (await repository.getRegisteredItems(
      keyword: '批量操作测试纸巾',
    ))
        .single;
    final milk =
        (await repository.getInventoryByWikiId(milkWiki.wikiId)).single;
    final tissue =
        (await repository.getInventoryByWikiId(tissueWiki.wikiId)).single;
    final ids = [milk.id, tissue.id];

    await repository.updateItemsStorageLocation(ids, '冷冻');
    expect((await repository.getItem(milk.id))?.storageLocation, '冷冻');
    expect((await repository.getItem(tissue.id))?.storageLocation, '冷冻');

    await repository.updateItemsCategory(ids, dailyCategory.id);
    expect(
        (await repository.getItem(milk.id))?.categoryName, dailyCategory.name);
    expect(
      (await repository.getItem(tissue.id))?.categoryName,
      dailyCategory.name,
    );

    await repository.markItemsAsConsumed(ids);
    final remainingMilk = await repository.getItem(milk.id);
    final consumedTissue = await repository.getItem(tissue.id);
    expect(remainingMilk?.status, ItemStatus.active);
    expect(remainingMilk?.quantity, 1);
    expect(consumedTissue?.status, ItemStatus.consumed);

    await repository.deleteItems(ids);
    expect(await repository.getItem(milk.id), isNull);
    expect(await repository.getItem(tissue.id), isNull);
  });

  test('generates shopping suggestions and converts checked items', () async {
    final categories = await repository.getCategories();
    final foodCategory = categories.firstWhere(
      (category) => category.name == '食品',
    );

    await repository.createItem(
      name: '采购建议测试豆腐',
      categoryId: foodCategory.id,
      quantity: 1,
      unit: '盒',
    );
    final registered = await repository.getRegisteredItems(
      keyword: '采购建议测试豆腐',
    );
    final item = (await repository.getInventoryByWikiId(
      registered.single.wikiId,
    ))
        .single;

    final suggestions = await repository.getShoppingSuggestions();
    final suggestion = suggestions.singleWhere(
      (suggestion) => suggestion.name == '采购建议测试豆腐',
    );
    expect(suggestion.reason, contains('低库存'));

    await repository.addShoppingSuggestion(suggestion);
    expect(
      (await repository.getShoppingSuggestions())
          .map((suggestion) => suggestion.name),
      isNot(contains('采购建议测试豆腐')),
    );

    final listItem = (await repository.getShoppingListItems())
        .singleWhere((item) => item.name == '采购建议测试豆腐');
    expect(listItem.quantity, 1);
    expect(listItem.categoryName, '食品');

    await repository.updateShoppingListItem(
      itemId: listItem.id,
      draft: ShoppingListDraft(
        name: listItem.name,
        categoryId: listItem.categoryId,
        sourceWikiId: listItem.sourceWikiId,
        quantity: 2,
        unit: listItem.unit,
        note: '买嫩一点',
        source: listItem.source,
      ),
    );
    await repository.setShoppingListItemChecked(
      listItem.id,
      isChecked: true,
    );

    final converted = await repository.convertCheckedShoppingItemsToInventory(
      purchaseDate: DateTime(2026, 6, 16),
    );
    expect(converted, 1);

    final openListItems = await repository.getShoppingListItems();
    expect(openListItems.map((item) => item.name), isNot(contains(item.name)));

    final batches = await repository.getInventoryByWikiId(
      registered.single.wikiId,
    );
    expect(batches.map((item) => item.quantity), contains(2));
    expect(batches.map((item) => item.sourceApp), contains('采购清单'));
    final convertedBatch = batches.singleWhere(
      (item) => item.sourceApp == '采购清单',
    );
    expect(convertedBatch.description, '买嫩一点');
    final wiki = await repository.getWiki(registered.single.wikiId);
    expect(wiki?.description, isNull);
  });

  test('runs app acceptance checks without leaving temporary data', () async {
    final report =
        await AcceptanceTestService(repository).runCoreInventoryChecks();

    expect(report.passed, isTrue);
    expect(report.checks, hasLength(15));
    expect(
      (await repository.getRegisteredItems(keyword: '应用自检测试物品-')),
      isEmpty,
    );
  });

  test('formats app self-check failures without technical prefixes', () {
    expect(
      selfCheckFailureMessage(StateError('没有可用分类')),
      '没有可用分类',
    );
    expect(
      selfCheckFailureMessage(ArgumentError('数量必须大于 0')),
      '数量必须大于 0',
    );
    expect(
      selfCheckFailureMessage(Exception('临时检查失败')),
      '临时检查失败',
    );
  });

  test('uses custom reminder days and returns today action items', () async {
    final categories = await repository.getCategories();
    final today = DateTime.now();

    await repository.createItem(
      name: '提醒测试牛奶',
      categoryId: categories.first.id,
      quantity: 1,
      unit: '盒',
      purchaseDate: today,
      expiryDate: today.add(const Duration(days: 5)),
      reminderDaysBefore: 5,
    );

    final registered = await repository.getRegisteredItems(
      keyword: '提醒测试牛奶',
    );
    final item =
        (await repository.getInventoryByWikiId(registered.single.wikiId))
            .single;
    expect(item.reminderDaysBefore, 5);
    expect(item.shouldRemind, isTrue);

    final todayActions = await repository.getTodayActionItems();
    expect(todayActions.map((item) => item.name), contains('提醒测试牛奶'));

    await repository.updateItem(
      itemId: item.id,
      quantity: 1,
      expiryDate: today.add(const Duration(days: 5)),
      isReminderEnabled: true,
      reminderDaysBefore: 2,
    );
    final updated = await repository.getItem(item.id);
    expect(updated?.reminderDaysBefore, 2);
    expect(updated?.shouldRemind, isFalse);
  });

  test('deduplicates reminder logs and hides ignored reminders today',
      () async {
    final categories = await repository.getCategories();
    final today = DateTime.now();

    await repository.createItem(
      name: '提醒去重测试牛奶',
      categoryId: categories.first.id,
      quantity: 1,
      unit: '盒',
      purchaseDate: today,
      expiryDate: today.add(const Duration(days: 3)),
      reminderDaysBefore: 3,
    );
    await repository.createItem(
      name: '稍后提醒测试酸奶',
      categoryId: categories.first.id,
      quantity: 1,
      unit: '盒',
      purchaseDate: today,
      expiryDate: today.add(const Duration(days: 3)),
      reminderDaysBefore: 3,
    );

    final milkWiki = (await repository.getRegisteredItems(
      keyword: '提醒去重测试牛奶',
    ))
        .single;
    final yogurtWiki = (await repository.getRegisteredItems(
      keyword: '稍后提醒测试酸奶',
    ))
        .single;
    final milk =
        (await repository.getInventoryByWikiId(milkWiki.wikiId)).single;
    final yogurt =
        (await repository.getInventoryByWikiId(yogurtWiki.wikiId)).single;

    final firstSent = await repository.recordReminderSentIfNeeded(
      itemId: milk.id,
      reminderType: 'reminder_due',
      message: '测试提醒',
      now: today,
    );
    final duplicateSent = await repository.recordReminderSentIfNeeded(
      itemId: milk.id,
      reminderType: 'reminder_due',
      message: '重复提醒',
      now: today,
    );

    expect(firstSent, isTrue);
    expect(duplicateSent, isFalse);

    await repository.ignoreReminderForToday(milk.id, now: today);
    await repository.snoozeReminder(yogurt.id, now: today);

    final todayActions = await repository.getTodayActionItems();
    expect(todayActions.map((item) => item.name), isNot(contains(milk.name)));
    expect(todayActions.map((item) => item.name), isNot(contains(yogurt.name)));
  });

  test(
    'builds pending local notification payloads for reminder items',
    () async {
      final categories = await repository.getCategories();
      final today = DateTime.now();

      await repository.createItem(
        name: '通知调度测试牛奶',
        categoryId: categories.first.id,
        quantity: 2,
        unit: '盒',
        purchaseDate: today,
        expiryDate: today.add(const Duration(days: 2)),
        storageLocation: '冷藏',
        reminderDaysBefore: 2,
      );
      await repository.createItem(
        name: '通知忽略测试面包',
        categoryId: categories.first.id,
        quantity: 1,
        unit: '袋',
        purchaseDate: today,
        expiryDate: today.add(const Duration(days: 2)),
        reminderDaysBefore: 2,
      );

      final milkWiki = (await repository.getRegisteredItems(
        keyword: '通知调度测试牛奶',
      ))
          .single;
      final breadWiki = (await repository.getRegisteredItems(
        keyword: '通知忽略测试面包',
      ))
          .single;
      final milk =
          (await repository.getInventoryByWikiId(milkWiki.wikiId)).single;
      final bread =
          (await repository.getInventoryByWikiId(breadWiki.wikiId)).single;
      await repository.ignoreReminderForToday(bread.id, now: today);

      final pending = await repository.getPendingReminderNotifications(
        now: today,
      );
      final notification = pending.singleWhere(
        (notification) => notification.itemId == milk.id,
      );

      expect(
        pending.map((notification) => notification.itemId),
        isNot(contains(bread.id)),
      );
      expect(notification.title, contains('通知调度测试牛奶'));
      expect(notification.body, contains('2盒'));
      expect(notification.body, contains('冷藏'));
      expect(notification.scheduledAt.isAfter(today), isTrue);
      expect(notification.toMap()['scheduledAtMillis'], isA<int>());
    },
  );

  test('uses wiki default reminder days for new inventory batches', () async {
    final milk = (await repository.getRegisteredItems(keyword: '鲜牛奶')).single;

    await repository.updateWiki(
      wikiId: milk.wikiId,
      name: milk.name,
      categoryId: milk.categoryId,
      defaultUnit: milk.defaultUnit,
      storageLocation: milk.storageLocation,
      defaultReminderDays: 1,
    );
    await repository.createItem(
      name: milk.name,
      categoryId: milk.categoryId,
      quantity: 1,
      unit: milk.defaultUnit,
      expiryDate: DateTime.now().add(const Duration(days: 4)),
    );

    final batches = await repository.getInventoryByWikiId(milk.wikiId);
    final created = batches
        .where((item) => item.quantity == 1 && item.reminderDaysBefore == 1)
        .toList();

    expect(created, hasLength(1));
    expect(created.single.shouldRemind, isFalse);
  });

  test('detects duplicate order imports and returns summary counts', () async {
    final controller = InventoryController(repository);
    await controller.initialize();
    final purchaseDate = DateTime(2026, 5, 1);
    final result = OrderRecognitionResult(
      sourceApp: '盒马',
      merchant: '盒马鲜生',
      orderId: 'ORDER-001',
      purchaseDate: purchaseDate,
      items: [
        const OrderRecognitionItem(
          name: '订单导入测试牛奶',
          quantity: 1,
          unit: '盒',
          categoryName: '食品',
          confidence: 0.91,
        ),
        const OrderRecognitionItem(
          name: '订单导入测试鸡蛋',
          quantity: 12,
          unit: '个',
          categoryName: '食品',
          confidence: 0.88,
        ),
      ],
    );

    final firstSummary = await controller.createItemsFromOrder(
      result: result,
      items: result.items,
      imagePath: '/tmp/order-001.png',
    );

    expect(firstSummary.addedCount, 2);
    expect(firstSummary.skippedCount, 0);
    expect(firstSummary.needsManualReviewCount, 0);

    final duplicates = await controller.findOrderImportDuplicates(
      result: result,
      items: result.items,
    );
    expect(duplicates, hasLength(2));
    expect(duplicates.map((row) => row.index), containsAll([0, 1]));

    final secondSummary = await controller.createItemsFromOrder(
      result: result,
      items: result.items,
      uncheckedCount: 1,
      needsManualReviewCount: 1,
    );

    expect(secondSummary.addedCount, 0);
    expect(secondSummary.duplicateCount, 2);
    expect(secondSummary.uncheckedCount, 1);
    expect(secondSummary.skippedCount, 3);
    expect(secondSummary.needsManualReviewCount, 1);

    final registered = await repository.getRegisteredItems(
      keyword: '订单导入测试牛奶',
    );
    expect(registered.single.activeBatchCount, 1);

    final importedItems =
        await repository.getInventoryByWikiId(registered.single.wikiId);
    expect(importedItems.single.sourceApp, '盒马');
    expect(importedItems.single.sourceOrderId, 'ORDER-001');
    expect(importedItems.single.importBatchId, 'ORDER-001');
    expect(importedItems.single.imagePath, '/tmp/order-001.png');
    expect(importedItems.single.recognitionConfidence, 0.91);

    const noDateResult = OrderRecognitionResult(
      sourceApp: '手动粘贴',
      merchant: '内测超市',
      orderId: 'ORDER-NODATE-001',
      items: [
        OrderRecognitionItem(
          name: '无日期重复苹果',
          quantity: 2,
          unit: '个',
          categoryName: '食品',
          confidence: 0.72,
        ),
      ],
    );
    final firstNoDateSummary = await controller.createItemsFromOrder(
      result: noDateResult,
      items: noDateResult.items,
    );
    expect(firstNoDateSummary.addedCount, 1);

    final noDateDuplicates = await controller.findOrderImportDuplicates(
      result: noDateResult,
      items: noDateResult.items,
    );
    expect(noDateDuplicates, hasLength(1));
    expect(noDateDuplicates.single.index, 0);
    expect(noDateDuplicates.single.purchaseDate, isNull);

    final secondNoDateSummary = await controller.createItemsFromOrder(
      result: noDateResult,
      items: noDateResult.items,
    );
    expect(secondNoDateSummary.addedCount, 0);
    expect(secondNoDateSummary.duplicateCount, 1);
  });

  test('exports and restores backup with a pre-restore snapshot', () async {
    final backup = await repository.exportBackup();
    final categories = await repository.getCategories();
    final backupData = backup['data'] as Map<String, Object?>;
    expect(backupData.keys, contains('app_metadata'));

    await repository.createItem(
      name: '备份后新增物品',
      categoryId: categories.first.id,
      quantity: 1,
      unit: '个',
      purchaseDate: DateTime(2026, 6, 17),
      expiryDate: DateTime(2026, 6, 30),
    );
    expect(
      await repository.getRegisteredItems(keyword: '备份后新增物品'),
      isNotEmpty,
    );
    final csv = await repository.exportInventoryCsv();
    expect(csv, startsWith('\ufeff物品名称,分类,状态,数量,单位,购买日期,过期日期,存放位置,标签,来源'));
    expect(csv, contains('备份后新增物品'));
    expect(csv, contains('2026-06-17,2026-06-30'));
    expect(csv, isNot(contains('T00:00')));
    expect(csv, isNot(contains('source_order_id')));
    expect(csv, isNot(startsWith('id,')));

    final result = await repository.restoreBackup(
      backup,
      replaceExisting: true,
    );

    expect(result.restoredRows, greaterThan(0));
    expect(result.preRestoreSnapshotId, isNotEmpty);
    expect(
      await repository.getRegisteredItems(keyword: '备份后新增物品'),
      isEmpty,
    );
    expect(await repository.getBackupSnapshots(), isNotEmpty);
    expect((await repository.checkDataHealth()).passed, isTrue);
  });

  test('rejects incomplete backup before changing current data', () async {
    final categories = await repository.getCategories();
    await repository.createItem(
      name: '坏备份保护测试物品',
      categoryId: categories.first.id,
      quantity: 1,
      unit: '个',
    );
    final snapshotsBefore = await repository.getBackupSnapshots();

    expect(
      () => repository.restoreBackup(
        {
          'data': {
            'items': <Map<String, Object?>>[],
          },
        },
        replaceExisting: true,
      ),
      throwsA(isA<FormatException>()),
    );

    expect(
      await repository.getRegisteredItems(keyword: '坏备份保护测试物品'),
      isNotEmpty,
    );
    expect(
      await repository.getBackupSnapshots(),
      hasLength(snapshotsBefore.length),
    );
  });

  test('prompts backup after large local changes and clears after export',
      () async {
    final categories = await repository.getCategories();
    for (var index = 0; index < 10; index += 1) {
      await repository.createItem(
        name: '备份提醒测试物品-$index',
        categoryId: categories.first.id,
        quantity: 1,
        unit: '个',
      );
    }

    final pending = await repository.getBackupReminderState();
    expect(pending.isPending, isTrue);
    expect(pending.dirtyCount, 10);
    expect(pending.message, contains('建议导出一份备份'));

    await repository.markBackupExported();
    final cleared = await repository.getBackupReminderState();
    expect(cleared.isPending, isFalse);
    expect(cleared.dirtyCount, 0);
    expect(cleared.lastExportedAt, isNotNull);
  });

  test('previews legacy import conflicts and logs import decisions', () async {
    final legacyPayload = <String, dynamic>{
      'categories': [
        {
          'id': 'cat-food',
          'name': '食品',
          'icon': 'restaurant',
          'color': '#1B8B7A',
          'sort_order': 1,
          'created_at': '2026-01-01T00:00:00.000',
          'updated_at': '2026-01-01T00:00:00.000',
        },
        {
          'id': 'cat-legacy',
          'name': 'legacy 分类',
          'icon': 'category',
          'color': '#000000',
          'sort_order': 9,
          'created_at': '2026-01-01T00:00:00.000',
          'updated_at': '2026-01-01T00:00:00.000',
        },
      ],
      'wikis': [
        {
          'id': 'wiki-legacy-tofu',
          'name': 'legacy 豆腐',
          'icon': null,
          'description': '迁移测试 Wiki',
          'category_id': 'cat-legacy',
          'default_unit': '盒',
          'suggested_expiry_days': 5,
          'storage_location': '冷藏',
          'notes': null,
          'image_path': null,
          'created_at': '2026-01-01T00:00:00.000',
          'updated_at': '2026-01-02T00:00:00.000',
        },
      ],
      'items': [
        {
          'id': 'item-legacy-tofu',
          'wiki_id': 'wiki-legacy-tofu',
          'name': 'legacy 豆腐',
          'description': null,
          'quantity': 2,
          'unit': '盒',
          'purchase_date': '2026-01-01T00:00:00.000',
          'expiry_date': '2026-01-06T00:00:00.000',
          'reminder_date': '2026-01-03T00:00:00.000',
          'status': 'active',
          'is_reminder_enabled': 1,
          'reminder_days_before': 3,
          'consumed_at': null,
          'predicted_expiry_date': null,
          'prediction_confidence': null,
          'recognition_confidence': null,
          'image_path': null,
          'storage_location': '冷藏',
          'source_app': 'legacy',
          'source_order_id': null,
          'import_batch_id': 'legacy-batch',
          'created_at': '2026-01-01T00:00:00.000',
          'updated_at': '2026-01-02T00:00:00.000',
        },
        {
          'id': 'item-broken',
          'wiki_id': 'missing-wiki',
          'name': '缺少 Wiki 的库存',
          'quantity': 1,
          'created_at': '2026-01-01T00:00:00.000',
          'updated_at': '2026-01-01T00:00:00.000',
        },
      ],
      'tags': [
        {
          'id': 'tag-legacy',
          'name': 'legacy 标签',
          'color': null,
          'created_at': '2026-01-01T00:00:00.000',
        },
      ],
      'item_tags': [
        {
          'item_id': 'item-legacy-tofu',
          'tag_id': 'tag-legacy',
          'created_at': '2026-01-01T00:00:00.000',
        },
      ],
    };

    final preview = await repository.previewLegacyImportData(legacyPayload);
    expect(preview.source.categories, 2);
    expect(preview.inserts.categories, 1);
    expect(preview.skipped.categories, 1);
    expect(preview.inserts.wikis, 1);
    expect(preview.inserts.items, 1);
    expect(preview.failedRows, 1);
    expect(preview.logs.map((log) => log.action), contains('failed'));

    final result = await repository.importLegacyData(
      legacyPayload,
      clearDemoBeforeImport: true,
    );

    expect(result.clearedDemoRows, greaterThan(0));
    expect(result.categories, 1);
    expect(result.wikis, 1);
    expect(result.items, 1);
    expect(result.tags, 1);
    expect(result.itemTags, 1);
    expect(result.skipped.categories, 1);
    expect(result.failedRows, 1);
    expect(result.healthPassed, isTrue);
    final backupReminder = await repository.getBackupReminderState();
    expect(backupReminder.isPending, isTrue);
    expect(backupReminder.reason, '旧版库存导入');
    expect(
      result.logs.map((log) => log.action),
      containsAll(['inserted', 'failed']),
    );

    final imported = await repository.getRegisteredItems(keyword: 'legacy 豆腐');
    expect(imported.single.totalQuantity, 2);
    expect(await repository.getRegisteredItems(keyword: '鲜牛奶'), isEmpty);
  });

  test('loads default legacy asset without probing missing local override',
      () async {
    const legacyAsset = 'assets/import/legacy_inventory.json';
    const localAsset = 'assets/import/legacy_inventory.local.json';
    final bundle = _FakeLegacyAssetBundle(
      manifestAssets: const [legacyAsset],
      assets: const {
        legacyAsset: '''
{
  "format": "vibe-fridge-legacy-export",
  "version": 1,
  "categories": [],
  "wikis": [],
  "items": [],
  "tags": [],
  "item_tags": []
}
''',
      },
    );
    final controller = InventoryController(repository, assetBundle: bundle);

    final preview = await controller.previewLegacyAssetImport();

    expect(preview.source.total, 0);
    expect(bundle.loadedAssets, contains(legacyAsset));
    expect(bundle.loadedAssets, isNot(contains(localAsset)));
  });

  test('reports invariant violations in health check', () async {
    final now = DateTime.now().toIso8601String();
    await appDatabase.database.insert('items', {
      'id': 'invalid-item',
      'wiki_id': 'wiki-milk',
      'name': '异常库存',
      'description': null,
      'quantity': 0,
      'unit': '个',
      'purchase_date': 'not-a-date',
      'expiry_date': null,
      'reminder_date': null,
      'status': 'active',
      'is_reminder_enabled': 1,
      'reminder_days_before': 3,
      'consumed_at': now,
      'predicted_expiry_date': null,
      'prediction_confidence': null,
      'recognition_confidence': null,
      'image_path': null,
      'storage_location': null,
      'source_app': null,
      'source_order_id': null,
      'import_batch_id': null,
      'created_at': now,
      'updated_at': now,
    });

    final health = await repository.checkDataHealth();

    expect(health.passed, isFalse);
    expect(
      health.issues.map((issue) => issue.code),
      containsAll([
        'non_positive_quantity',
        'active_with_consumed_at',
        'invalid_date',
      ]),
    );
  });

  test(
    'keeps dashboard and catalog queries responsive with 1500 items',
    () async {
      final categories = await repository.getCategories();
      final categoryId = categories.first.id;
      final now = DateTime.now();
      final nowText = now.toIso8601String();
      final today = DateTime(now.year, now.month, now.day);

      String dateText(DateTime value) {
        return DateTime(value.year, value.month, value.day).toIso8601String();
      }

      await appDatabase.database.transaction((txn) async {
        final batch = txn.batch();
        for (var index = 0; index < 1500; index += 1) {
          final wikiId = 'perf-wiki-$index';
          final itemId = 'perf-item-$index';
          final expiryDate = today.add(Duration(days: index % 21 - 5));
          final reminderDate = expiryDate.subtract(const Duration(days: 3));
          final name = '性能测试苹果${index.toString().padLeft(4, '0')}';
          batch.insert('item_wikis', {
            'id': wikiId,
            'name': name,
            'icon': null,
            'description': '性能测试数据',
            'category_id': categoryId,
            'default_unit': '个',
            'suggested_expiry_days': 14,
            'storage_location': '冷藏',
            'default_reminder_days': 3,
            'notes': null,
            'image_path': null,
            'created_at': nowText,
            'updated_at': nowText,
          });
          batch.insert('items', {
            'id': itemId,
            'wiki_id': wikiId,
            'name': name,
            'description': null,
            'quantity': index % 5 + 1,
            'unit': '个',
            'purchase_date': dateText(today.subtract(const Duration(days: 2))),
            'expiry_date': dateText(expiryDate),
            'reminder_date': dateText(reminderDate),
            'status': ItemStatus.active.dbValue,
            'is_reminder_enabled': 1,
            'reminder_days_before': 3,
            'consumed_at': null,
            'predicted_expiry_date': null,
            'prediction_confidence': null,
            'recognition_confidence': null,
            'image_path': null,
            'storage_location': '冷藏',
            'source_app': null,
            'source_order_id': null,
            'import_batch_id': null,
            'created_at': nowText,
            'updated_at': nowText,
          });
          if (index % 10 == 0) {
            batch.insert('reminder_logs', {
              'id': 'perf-reminder-$index',
              'item_id': itemId,
              'reminder_type': 'ignored',
              'message': '性能测试忽略',
              'sent_at': today.add(const Duration(hours: 8)).toIso8601String(),
              'is_success': 1,
              'error_message': null,
            });
          }
        }
        await batch.commit(noResult: true);
      });

      final stopwatch = Stopwatch()..start();
      final controller = InventoryController(repository);
      await controller.refresh();
      final refreshElapsed = stopwatch.elapsedMilliseconds;

      stopwatch
        ..reset()
        ..start();
      final searchResults = await repository.getRegisteredItems(
        keyword: '性能测试苹果1499',
      );
      final searchElapsed = stopwatch.elapsedMilliseconds;

      stopwatch
        ..reset()
        ..start();
      final categoryResults = await repository.getRegisteredItems(
        categoryId: categoryId,
      );
      final categoryElapsed = stopwatch.elapsedMilliseconds;
      stopwatch.stop();

      expect(controller.stats.registeredWikiCount, greaterThanOrEqualTo(1500));
      expect(controller.stats.activeBatchCount, greaterThanOrEqualTo(1500));
      expect(controller.todayActionItems.length, lessThanOrEqualTo(20));
      expect(
        searchResults.map((item) => item.name),
        contains('性能测试苹果1499'),
      );
      expect(categoryResults.length, greaterThanOrEqualTo(1500));
      expect(
        refreshElapsed,
        lessThan(4000),
        reason: 'dashboard refresh should stay responsive at 1500 items',
      );
      expect(
        searchElapsed,
        lessThan(1500),
        reason: 'exact catalog search should stay responsive at 1500 items',
      );
      expect(
        categoryElapsed,
        lessThan(3000),
        reason: 'category catalog query should stay responsive at 1500 items',
      );
    },
  );
}

class _FakeLegacyAssetBundle extends CachingAssetBundle {
  _FakeLegacyAssetBundle({
    required List<String> manifestAssets,
    required Map<String, String> assets,
  })  : _assets = assets,
        _manifestData = _encodeManifest(manifestAssets);

  final Map<String, String> _assets;
  final ByteData _manifestData;
  final loadedAssets = <String>[];

  static ByteData _encodeManifest(List<String> assets) {
    final manifest = <String, Object>{
      for (final asset in assets)
        asset: [
          <String, Object>{'asset': asset},
        ],
    };
    return const StandardMessageCodec().encodeMessage(manifest)!;
  }

  @override
  Future<ByteData> load(String key) async {
    loadedAssets.add(key);
    if (key == 'AssetManifest.bin') {
      return _manifestData;
    }
    final content = _assets[key];
    if (content == null) {
      throw StateError('Missing fake asset: $key');
    }
    return ByteData.sublistView(Uint8List.fromList(utf8.encode(content)));
  }
}
