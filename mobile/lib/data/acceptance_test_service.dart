import '../models/inventory_item.dart';
import '../models/item_status.dart';
import '../models/registered_item.dart';
import '../models/shopping_list_item.dart';
import 'ai_recipe_service.dart';
import 'inventory_repository.dart';
import 'recipe_preferences_store.dart';
import 'recipe_suggestion_service.dart';
import 'vlm_settings_store.dart';

class AcceptanceTestService {
  AcceptanceTestService(this.repository);

  final InventoryRepository repository;

  Future<AcceptanceReport> runCoreInventoryChecks() async {
    final startedAt = DateTime.now();
    final checks = <AcceptanceCheckResult>[];
    final testName = '应用自检测试物品-${startedAt.microsecondsSinceEpoch}';
    const testNamePrefix = '应用自检测试物品-';
    String? wikiId;
    String? originalItemId;
    String? restoredItemId;

    Future<void> check(
      String name,
      Future<void> Function() body,
    ) async {
      final stopwatch = Stopwatch()..start();
      try {
        await body();
        checks.add(
          AcceptanceCheckResult.passed(
            name: name,
            duration: stopwatch.elapsed,
          ),
        );
      } catch (error) {
        checks.add(
          AcceptanceCheckResult.failed(
            name: name,
            duration: stopwatch.elapsed,
            message: selfCheckFailureMessage(error),
          ),
        );
      }
    }

    await _cleanupTemporaryData(testNamePrefix);

    await check('默认分类和物品资料可读', () async {
      await repository.seedDefaults();
      final categories = await repository.getCategories();
      if (categories.isEmpty) {
        throw StateError('没有可用分类');
      }
      final stats = await repository.getStats();
      if (stats.registeredWikiCount == 0) {
        throw StateError('没有可用物品资料');
      }
    });

    await check('创建库存并自动关联物品资料', () async {
      final categories = await repository.getCategories();
      await repository.createItem(
        name: testName,
        categoryId: categories.isEmpty ? null : categories.first.id,
        description: '应用自检临时数据',
        quantity: 2,
        unit: '份',
        purchaseDate: startedAt,
        expiryDate: startedAt.add(const Duration(days: 3)),
        imagePath: '/tmp/vibe-fridge-acceptance/package.jpg',
        storageLocation: '冷藏',
        tags: const ['临期优先'],
      );

      final registered = await _singleRegisteredItem(testName);
      if (registered.activeBatchCount != 1 || registered.totalQuantity != 2) {
        throw StateError('创建后统计不正确');
      }
      wikiId = registered.wikiId;

      final item = await _activeItem(registered.wikiId);
      originalItemId = item.id;
      if (item.reminderDate == null || !item.isReminderEnabled) {
        throw StateError('提醒日期或提醒开关未正确初始化');
      }
      if (item.imagePath != '/tmp/vibe-fridge-acceptance/package.jpg') {
        throw StateError('图片附件未正确保存');
      }
      if (item.storageLocation != '冷藏') {
        throw StateError('存放位置未正确保存');
      }
      if (!item.tags.contains('临期优先')) {
        throw StateError('标签未正确保存');
      }
    });

    await check('今天要处理聚合包含提醒到期库存', () async {
      final actions = await repository.getTodayActionItems();
      final included = actions.any((item) => item.name == testName);
      if (!included) {
        throw StateError('3 天后过期的测试库存未进入今天要处理');
      }
    });

    await check('本地通知内容可基于提醒生成', () async {
      final item = await _activeItem(_required(wikiId, '物品资料'));
      final pending = await repository.getPendingReminderNotifications();
      PendingReminderNotification? notification;
      for (final candidate in pending) {
        if (candidate.itemId == item.id) {
          notification = candidate;
          break;
        }
      }
      if (notification == null) {
        throw StateError('没有为提醒到期库存生成本地通知内容');
      }
      if (notification.title.isEmpty ||
          notification.body.isEmpty ||
          notification.scheduledAt.isBefore(startedAt)) {
        throw StateError('本地通知内容无效');
      }
    });

    await check('提醒日志防重复并支持忽略本次', () async {
      final item = await _activeItem(_required(wikiId, '物品资料'));
      final firstSent = await repository.recordReminderSentIfNeeded(
        itemId: item.id,
        reminderType: 'reminder_due',
        message: '应用自检提醒',
      );
      final duplicateSent = await repository.recordReminderSentIfNeeded(
        itemId: item.id,
        reminderType: 'reminder_due',
        message: '应用自检重复提醒',
      );
      if (!firstSent || duplicateSent) {
        throw StateError('同日同类型提醒没有正确去重');
      }

      await repository.ignoreReminderForToday(item.id);
      final actions = await repository.getTodayActionItems();
      if (actions.any((action) => action.id == item.id)) {
        throw StateError('忽略本次后仍出现在今天要处理');
      }
    });

    await check('规则食谱建议可基于库存生成', () async {
      final activeItems = await repository.getActiveItems(limit: 50);
      final suggestions = RecipeSuggestionService().generate(activeItems);
      if (suggestions.isEmpty) {
        throw StateError('没有生成任何食谱建议');
      }
      final includesTestItem = suggestions.any((suggestion) {
        return suggestion.inventoryUses.any((use) => use.item.name == testName);
      });
      if (!includesTestItem) {
        throw StateError('食谱建议未使用临时测试库存');
      }
    });

    await check('AI 食谱不可用时回退到规则建议', () async {
      final activeItems = await repository.getActiveItems(limit: 50);
      final service = AiRecipeService();
      try {
        final result = await service.generate(
          items: activeItems,
          preferences: const RecipePreferences(),
          settings: const VlmSettings(endpoint: '', model: '', apiKey: ''),
        );
        if (!result.usedFallback || result.suggestions.isEmpty) {
          throw StateError('AI 食谱失败时没有回退到规则建议');
        }
      } finally {
        service.close();
      }
    });

    await check('采购清单可添加并转为库存', () async {
      final categories = await repository.getCategories();
      final suggestionName = '$testName-建议';
      await repository.createItem(
        name: suggestionName,
        categoryId: categories.isEmpty ? null : categories.first.id,
        quantity: 1,
        unit: '份',
      );
      final suggestions = await repository.getShoppingSuggestions();
      if (!suggestions.any((suggestion) => suggestion.name == suggestionName)) {
        throw StateError('临时低库存物品没有生成采购建议');
      }
      final shoppingName = '$testName-采购';
      final itemId = await repository.addShoppingListItem(
        ShoppingListDraft(
          name: shoppingName,
          categoryId: categories.isEmpty ? null : categories.first.id,
          quantity: 1,
          unit: '份',
          note: '应用自检补货',
          source: '应用自检',
        ),
      );

      final listItem = (await repository.getShoppingListItems())
          .singleWhere((item) => item.id == itemId);
      if (listItem.name != shoppingName || listItem.quantity != 1) {
        throw StateError('采购清单写入不正确');
      }

      await repository.setShoppingListItemChecked(itemId, isChecked: true);
      final converted = await repository.convertCheckedShoppingItemsToInventory(
        purchaseDate: startedAt,
        itemIds: [itemId],
      );
      if (converted != 1) {
        throw StateError('已买到采购项没有正确入库');
      }
      final registered = await repository.getRegisteredItems(
        keyword: shoppingName,
      );
      if (registered.isEmpty || registered.single.totalQuantity != 1) {
        throw StateError('采购项转库存后无法读取');
      }
    });

    await check('更新库存数量', () async {
      final item = await _activeItem(_required(wikiId, '物品资料'));
      await repository.updateItemQuantity(item.id, 1);
      final updated = await repository.getItem(item.id);
      if (updated == null || updated.quantity != 3) {
        throw StateError('数量更新后不是 3');
      }
      originalItemId = item.id;
    });

    await check('批量修改位置和分类', () async {
      final item = await _activeItem(_required(wikiId, '物品资料'));
      final categories = await repository.getCategories();
      final targetCategory = categories.firstWhere(
        (category) => category.name == '日用品',
        orElse: () => categories.first,
      );
      await repository.updateItemsStorageLocation([item.id], '冷冻');
      await repository.updateItemsCategory([item.id], targetCategory.id);

      final updated = await repository.getItem(item.id);
      if (updated == null ||
          updated.storageLocation != '冷冻' ||
          updated.categoryName != targetCategory.name) {
        throw StateError('批量修改位置或分类未正确保存');
      }
      originalItemId = item.id;
    });

    await check('标记消耗并写入历史', () async {
      final itemId = _required(originalItemId, '库存记录');
      await repository.markAsConsumed(itemId);
      final active = await repository.getItem(itemId);
      if (active == null ||
          active.quantity != 2 ||
          active.status != ItemStatus.active) {
        throw StateError('消耗后原批次数量或状态不正确');
      }

      final consumed = await _consumedItem(testName);
      if (consumed.quantity != 1) {
        throw StateError('消耗历史数量不正确');
      }
      restoredItemId = consumed.id;
    });

    await check('恢复已消耗记录', () async {
      final itemId = _required(restoredItemId, '已消耗记录');
      await repository.restoreItem(itemId);
      final restored = await repository.getItem(itemId);
      if (restored == null || restored.status != ItemStatus.active) {
        throw StateError('恢复后记录未回到使用中状态');
      }
    });

    await check('删除恢复后的库存记录', () async {
      final itemId = _required(restoredItemId, '已恢复记录');
      await repository.deleteItem(itemId);
      final deleted = await repository.getItem(itemId);
      if (deleted != null) {
        throw StateError('删除后仍能读取库存记录');
      }
    });

    await check('清理自检临时数据', () async {
      await _cleanupTemporaryData(testNamePrefix);
      final remaining = await repository.getRegisteredItems(
        keyword: testNamePrefix,
      );
      if (remaining.any((item) => item.name.startsWith(testNamePrefix))) {
        throw StateError('临时测试数据未清理干净');
      }
    });

    await check('资料一致性检查通过', () async {
      final health = await repository.checkDataHealth();
      if (!health.passed) {
        throw StateError(health.summary);
      }
    });

    return AcceptanceReport(
      startedAt: startedAt,
      completedAt: DateTime.now(),
      checks: checks,
    );
  }

  Future<RegisteredItem> _singleRegisteredItem(String name) async {
    final matches = await repository.getRegisteredItems(keyword: name);
    final exactMatches = matches.where((item) => item.name == name).toList();
    if (exactMatches.length != 1) {
      throw StateError('期望找到 1 个物品资料，实际为 ${exactMatches.length}');
    }
    return exactMatches.single;
  }

  Future<InventoryItem> _activeItem(String wikiId) async {
    final items = await repository.getInventoryByWikiId(wikiId);
    final activeItems = items
        .where(
          (item) =>
              item.status == ItemStatus.active &&
              item.name.startsWith('应用自检测试物品-'),
        )
        .toList();
    if (activeItems.isEmpty) {
      throw StateError('没有找到使用中的自检库存记录');
    }
    return activeItems.first;
  }

  Future<void> _cleanupTemporaryData(String namePrefix) async {
    final shoppingItems = await repository.getShoppingListItems(
      includeConverted: true,
    );
    for (final item in shoppingItems.where(
      (item) => item.name.startsWith(namePrefix),
    )) {
      await repository.deleteShoppingListItem(item.id);
    }

    final registeredItems = await repository.getRegisteredItems(
      keyword: namePrefix,
    );
    for (final item in registeredItems.where(
      (item) => item.name.startsWith(namePrefix),
    )) {
      await repository.deleteWiki(item.wikiId, force: true);
    }
  }

  Future<InventoryItem> _consumedItem(String name) async {
    final history = await repository.getHistoryItems(limit: 100);
    final matches = history
        .where(
            (item) => item.name == name && item.status == ItemStatus.consumed)
        .toList();
    if (matches.length != 1) {
      throw StateError('期望找到 1 条消耗历史，实际为 ${matches.length}');
    }
    return matches.single;
  }

  String _required(String? value, String label) {
    if (value == null) {
      throw StateError('前置检查未产生 $label');
    }
    return value;
  }
}

String selfCheckFailureMessage(Object error) {
  var message = error.toString().trim();
  const prefixes = [
    'Bad state: ',
    'Invalid argument(s): ',
    'Exception: ',
    'FormatException: ',
  ];
  for (final prefix in prefixes) {
    if (message.startsWith(prefix)) {
      message = message.substring(prefix.length).trim();
      break;
    }
  }
  if (message.isEmpty) {
    return '检查没有完成，请稍后重试';
  }
  return message;
}

class AcceptanceReport {
  const AcceptanceReport({
    required this.startedAt,
    required this.completedAt,
    required this.checks,
  });

  final DateTime startedAt;
  final DateTime completedAt;
  final List<AcceptanceCheckResult> checks;

  bool get passed => checks.every((check) => check.passed);
  int get passedCount => checks.where((check) => check.passed).length;
  Duration get duration => completedAt.difference(startedAt);
}

class AcceptanceCheckResult {
  const AcceptanceCheckResult._({
    required this.name,
    required this.passed,
    required this.duration,
    this.message,
  });

  factory AcceptanceCheckResult.passed({
    required String name,
    required Duration duration,
  }) {
    return AcceptanceCheckResult._(
      name: name,
      passed: true,
      duration: duration,
    );
  }

  factory AcceptanceCheckResult.failed({
    required String name,
    required Duration duration,
    required String message,
  }) {
    return AcceptanceCheckResult._(
      name: name,
      passed: false,
      duration: duration,
      message: message,
    );
  }

  final String name;
  final bool passed;
  final Duration duration;
  final String? message;
}
