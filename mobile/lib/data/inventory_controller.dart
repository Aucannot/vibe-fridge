import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../models/inventory_item.dart';
import '../models/inventory_stats.dart';
import '../models/item_status.dart';
import '../models/item_wiki_category.dart';
import '../models/order_recognition.dart';
import '../models/registered_item.dart';
import '../models/shopping_list_item.dart';
import 'acceptance_test_service.dart';
import 'inventory_repository.dart';
import 'local_notification_service.dart';

class InventoryController extends ChangeNotifier {
  InventoryController(
    this.repository, {
    LocalNotificationService? notificationService,
    AssetBundle? assetBundle,
  })  : notificationService = notificationService ?? LocalNotificationService(),
        assetBundle = assetBundle ?? rootBundle {
    this.notificationService.setOnNotificationTap(_handleNotificationTap);
  }

  final InventoryRepository repository;
  final LocalNotificationService notificationService;
  final AssetBundle assetBundle;

  bool isLoading = true;
  String? errorMessage;
  List<ItemWikiCategory> categories = [];
  List<RegisteredItem> registeredItems = [];
  List<InventoryItem> activeItems = [];
  List<InventoryItem> expiringItems = [];
  List<InventoryItem> todayActionItems = [];
  List<InventoryItem> historyItems = [];
  List<ShoppingListItem> shoppingListItems = [];
  List<ShoppingSuggestion> shoppingSuggestions = [];
  InventoryStats stats = InventoryStats.empty;
  BackupReminderState backupReminderState = BackupReminderState.none;
  LocalNotificationPermissionSnapshot notificationPermission =
      LocalNotificationPermissionSnapshot.unknown;
  LocalNotificationSyncResult? lastNotificationSyncResult;
  String? _notificationTappedItemId;

  Future<void> initialize() async {
    await repository.seedDefaults();
    await refresh();
    await _loadNotificationLaunchTarget();
  }

  Future<void> refresh() async {
    isLoading = true;
    errorMessage = null;
    notifyListeners();

    try {
      final results = await Future.wait([
        repository.getCategories(),
        repository.getRegisteredItems(),
        repository.getActiveItems(limit: 20),
        repository.getExpiringItems(days: 7),
        repository.getTodayActionItems(limit: 20),
        repository.getHistoryItems(limit: 50),
        repository.getShoppingListItems(),
        repository.getShoppingSuggestions(),
        repository.getStats(),
        repository.getBackupReminderState(),
      ]);
      categories = results[0] as List<ItemWikiCategory>;
      registeredItems = results[1] as List<RegisteredItem>;
      activeItems = results[2] as List<InventoryItem>;
      expiringItems = results[3] as List<InventoryItem>;
      todayActionItems = results[4] as List<InventoryItem>;
      historyItems = results[5] as List<InventoryItem>;
      shoppingListItems = results[6] as List<ShoppingListItem>;
      shoppingSuggestions = results[7] as List<ShoppingSuggestion>;
      stats = results[8] as InventoryStats;
      backupReminderState = results[9] as BackupReminderState;
    } catch (error) {
      errorMessage = error.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
    await _syncAfterRefreshSilently();
  }

  Future<List<RegisteredItem>> searchRegisteredItems({
    String? categoryId,
    String? keyword,
  }) {
    return repository.getRegisteredItems(
        categoryId: categoryId, keyword: keyword);
  }

  Future<void> createItem({
    required String name,
    String? categoryId,
    String? description,
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
  }) async {
    await repository.createItem(
      name: name,
      categoryId: categoryId,
      description: description,
      quantity: quantity,
      unit: unit,
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
      predictedExpiryDate: predictedExpiryDate,
      predictionConfidence: predictionConfidence,
      recognitionConfidence: recognitionConfidence,
      imagePath: imagePath,
      storageLocation: storageLocation,
      tags: tags,
      sourceApp: sourceApp,
      sourceOrderId: sourceOrderId,
      importBatchId: importBatchId,
    );
    await refresh();
  }

  Future<List<OrderImportDuplicate>> findOrderImportDuplicates({
    required OrderRecognitionResult result,
    required List<OrderRecognitionItem> items,
  }) async {
    final sourceOrderId = result.orderId?.trim();
    if (sourceOrderId == null || sourceOrderId.isEmpty) {
      return const [];
    }

    final duplicates = <OrderImportDuplicate>[];
    for (var index = 0; index < items.length; index += 1) {
      final item = items[index];
      final purchaseDate = item.purchaseDate ?? result.purchaseDate;
      if (item.name.trim().isEmpty) {
        continue;
      }
      final count = await repository.countOrderImportDuplicates(
        sourceOrderId: sourceOrderId,
        name: item.name,
        purchaseDate: purchaseDate,
      );
      if (count > 0) {
        duplicates.add(
          OrderImportDuplicate(
            index: index,
            name: item.name,
            purchaseDate: purchaseDate,
            existingCount: count,
          ),
        );
      }
    }
    return duplicates;
  }

  Future<OrderImportSummary> createItemsFromOrder({
    required OrderRecognitionResult result,
    required Iterable<OrderRecognitionItem> items,
    String? imagePath,
    int uncheckedCount = 0,
    int duplicateSkippedBeforeImport = 0,
    int needsManualReviewCount = 0,
  }) async {
    var addedCount = 0;
    var duplicateCount = duplicateSkippedBeforeImport;
    final sourceApp = result.sourceApp ?? result.merchant;
    final sourceOrderId = result.orderId;
    for (final item in items) {
      final purchaseDate = item.purchaseDate ?? result.purchaseDate;
      if (sourceOrderId != null && sourceOrderId.trim().isNotEmpty) {
        final duplicates = await repository.countOrderImportDuplicates(
          sourceOrderId: sourceOrderId,
          name: item.name,
          purchaseDate: purchaseDate,
        );
        if (duplicates > 0) {
          duplicateCount += 1;
          continue;
        }
      }
      await repository.createItem(
        name: item.name,
        categoryId: _categoryIdForName(item.categoryName),
        description: item.notes,
        quantity: item.quantity,
        unit: item.unit,
        purchaseDate: purchaseDate,
        expiryDate: item.inventoryExpiryDate,
        predictedExpiryDate: item.predictedExpiryDate,
        predictionConfidence: item.confidence,
        recognitionConfidence: item.confidence,
        imagePath: imagePath,
        sourceApp: sourceApp,
        sourceOrderId: sourceOrderId,
        importBatchId: sourceOrderId,
      );
      addedCount += 1;
    }
    await refresh();
    return OrderImportSummary(
      addedCount: addedCount,
      uncheckedCount: uncheckedCount,
      duplicateCount: duplicateCount,
      needsManualReviewCount: needsManualReviewCount,
    );
  }

  Future<void> updateItemQuantity(String itemId, int delta) async {
    await repository.updateItemQuantity(itemId, delta);
    await refresh();
  }

  Future<void> markAsConsumed(String itemId) async {
    await repository.markAsConsumed(itemId);
    await refresh();
  }

  Future<void> markItemsAsConsumed(Iterable<String> itemIds) async {
    await repository.markItemsAsConsumed(itemIds);
    await refresh();
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
    await repository.updateItem(
      itemId: itemId,
      quantity: quantity,
      unit: unit,
      description: description,
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
      imagePath: imagePath,
      storageLocation: storageLocation,
      tags: tags,
      isReminderEnabled: isReminderEnabled,
      reminderDaysBefore: reminderDaysBefore,
    );
    await refresh();
  }

  Future<void> deleteItem(String itemId) async {
    await repository.deleteItem(itemId);
    await refresh();
  }

  Future<void> deleteItems(Iterable<String> itemIds) async {
    await repository.deleteItems(itemIds);
    await refresh();
  }

  Future<void> addShoppingListItem(ShoppingListDraft draft) async {
    await repository.addShoppingListItem(draft);
    await refresh();
  }

  Future<void> addShoppingSuggestion(ShoppingSuggestion suggestion) async {
    await repository.addShoppingSuggestion(suggestion);
    await refresh();
  }

  Future<void> addRegisteredItemToShoppingList(RegisteredItem item) {
    return addShoppingListItem(
      ShoppingListDraft(
        name: item.name,
        categoryId: item.categoryId,
        sourceWikiId: item.wikiId,
        quantity: 1,
        unit: item.defaultUnit,
        note: '从物品目录加入',
      ),
    );
  }

  Future<void> addInventoryItemToShoppingList(InventoryItem item) {
    return addShoppingListItem(
      ShoppingListDraft(
        name: item.name,
        sourceWikiId: item.wikiId,
        sourceItemId: item.id,
        quantity: 1,
        unit: item.unit,
        note: item.status == ItemStatus.consumed ? '上次已消耗' : '从库存记录加入',
      ),
    );
  }

  Future<void> updateShoppingListItem({
    required String itemId,
    required ShoppingListDraft draft,
  }) async {
    await repository.updateShoppingListItem(itemId: itemId, draft: draft);
    await refresh();
  }

  Future<void> setShoppingListItemChecked(
    String itemId, {
    required bool isChecked,
  }) async {
    await repository.setShoppingListItemChecked(
      itemId,
      isChecked: isChecked,
    );
    await refresh();
  }

  Future<void> deleteShoppingListItem(String itemId) async {
    await repository.deleteShoppingListItem(itemId);
    await refresh();
  }

  Future<int> convertCheckedShoppingItemsToInventory() async {
    final converted = await repository.convertCheckedShoppingItemsToInventory();
    await refresh();
    return converted;
  }

  Future<void> updateItemsStorageLocation(
    Iterable<String> itemIds,
    String? storageLocation,
  ) async {
    await repository.updateItemsStorageLocation(itemIds, storageLocation);
    await refresh();
  }

  Future<void> updateItemsCategory(
    Iterable<String> itemIds,
    String? categoryId,
  ) async {
    await repository.updateItemsCategory(itemIds, categoryId);
    await refresh();
  }

  Future<void> restoreItem(String itemId) async {
    await repository.restoreItem(itemId);
    await refresh();
  }

  Future<bool> recordReminderSentIfNeeded({
    required String itemId,
    required String reminderType,
    required String message,
  }) {
    return repository.recordReminderSentIfNeeded(
      itemId: itemId,
      reminderType: reminderType,
      message: message,
    );
  }

  Future<LocalNotificationPermissionSnapshot>
      requestNotificationPermission() async {
    notificationPermission = await notificationService.requestPermission();
    notifyListeners();
    if (notificationPermission.granted) {
      await syncLocalNotifications();
    }
    return notificationPermission;
  }

  Future<LocalNotificationSyncResult> syncLocalNotifications({
    bool silent = false,
  }) async {
    final result = await notificationService.syncInventoryReminders(repository);
    notificationPermission = result.permission;
    lastNotificationSyncResult = result;
    if (!silent) {
      notifyListeners();
    }
    return result;
  }

  String? consumeNotificationTappedItemId() {
    final itemId = _notificationTappedItemId;
    _notificationTappedItemId = null;
    return itemId;
  }

  void _handleNotificationTap(String itemId) {
    _notificationTappedItemId = itemId;
    notifyListeners();
  }

  Future<void> _loadNotificationLaunchTarget() async {
    final itemId = await notificationService.getLaunchItemId();
    if (itemId != null) {
      _notificationTappedItemId = itemId;
    }
  }

  Future<void> snoozeReminder(String itemId) async {
    await repository.snoozeReminder(itemId);
    await refresh();
  }

  Future<void> ignoreReminderForToday(String itemId) async {
    await repository.ignoreReminderForToday(itemId);
    await refresh();
  }

  Future<void> _syncAfterRefreshSilently() async {
    try {
      await syncLocalNotifications(silent: true);
    } catch (_) {
      return;
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
    int? defaultReminderDays,
    String? storageLocation,
    String? notes,
  }) async {
    await repository.updateWiki(
      wikiId: wikiId,
      name: name,
      categoryId: categoryId,
      icon: icon,
      description: description,
      defaultUnit: defaultUnit,
      suggestedExpiryDays: suggestedExpiryDays,
      defaultReminderDays: defaultReminderDays,
      storageLocation: storageLocation,
      notes: notes,
    );
    await refresh();
  }

  Future<void> deleteWiki(String wikiId, {bool force = false}) async {
    await repository.deleteWiki(wikiId, force: force);
    await refresh();
  }

  Future<LegacyImportPreview> previewLegacyAssetImport() async {
    final raw = await _loadLegacyImportAsset();
    final payload = jsonDecode(raw) as Map<String, dynamic>;
    return repository.previewLegacyImportData(payload);
  }

  Future<LegacyImportResult> importLegacyAsset({
    bool clearDemoBeforeImport = false,
  }) async {
    final raw = await _loadLegacyImportAsset();
    final payload = jsonDecode(raw) as Map<String, dynamic>;
    final result = await repository.importLegacyData(
      payload,
      clearDemoBeforeImport: clearDemoBeforeImport,
    );
    await refresh();
    return result;
  }

  Future<AcceptanceReport> runAcceptanceChecks() async {
    final result =
        await AcceptanceTestService(repository).runCoreInventoryChecks();
    await refresh();
    return result;
  }

  Future<int> resetDemoData() async {
    final clearedRows = await repository.resetDemoData();
    await refresh();
    return clearedRows;
  }

  Future<Map<String, dynamic>> exportBackup() {
    return repository.exportBackup();
  }

  Future<void> markBackupExported() async {
    await repository.markBackupExported();
    await refresh();
  }

  Future<String> exportInventoryCsv() {
    return repository.exportInventoryCsv();
  }

  Future<BackupRestoreResult> restoreBackup(
    Map<String, dynamic> backup, {
    bool replaceExisting = true,
  }) async {
    final result = await repository.restoreBackup(
      backup,
      replaceExisting: replaceExisting,
    );
    await refresh();
    return result;
  }

  Future<String> _loadLegacyImportAsset() async {
    const localAsset = 'assets/import/legacy_inventory.local.json';
    const defaultAsset = 'assets/import/legacy_inventory.json';
    final manifest = await AssetManifest.loadFromAssetBundle(assetBundle);
    if (manifest.listAssets().contains(localAsset)) {
      return assetBundle.loadString(localAsset);
    }
    return assetBundle.loadString(defaultAsset);
  }

  String? _categoryIdForName(String? categoryName) {
    final normalized = categoryName?.trim();
    if (normalized == null || normalized.isEmpty) {
      return null;
    }
    for (final category in categories) {
      if (category.name == normalized) {
        return category.id;
      }
    }
    for (final category in categories) {
      if (normalized.contains(category.name) ||
          category.name.contains(normalized)) {
        return category.id;
      }
    }
    return null;
  }
}

class OrderImportDuplicate {
  const OrderImportDuplicate({
    required this.index,
    required this.name,
    required this.purchaseDate,
    required this.existingCount,
  });

  final int index;
  final String name;
  final DateTime? purchaseDate;
  final int existingCount;
}

class OrderImportSummary {
  const OrderImportSummary({
    required this.addedCount,
    required this.uncheckedCount,
    required this.duplicateCount,
    required this.needsManualReviewCount,
  });

  final int addedCount;
  final int uncheckedCount;
  final int duplicateCount;
  final int needsManualReviewCount;

  int get skippedCount => uncheckedCount + duplicateCount;
}
