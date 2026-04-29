import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter/services.dart';

import '../models/inventory_item.dart';
import '../models/inventory_stats.dart';
import '../models/item_wiki_category.dart';
import '../models/registered_item.dart';
import 'inventory_repository.dart';

class InventoryController extends ChangeNotifier {
  InventoryController(this.repository);

  final InventoryRepository repository;

  bool isLoading = true;
  String? errorMessage;
  List<ItemWikiCategory> categories = [];
  List<RegisteredItem> registeredItems = [];
  List<InventoryItem> activeItems = [];
  List<InventoryItem> expiringItems = [];
  List<InventoryItem> historyItems = [];
  InventoryStats stats = InventoryStats.empty;

  Future<void> initialize() async {
    await repository.seedDefaults();
    await refresh();
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
        repository.getHistoryItems(limit: 50),
        repository.getStats(),
      ]);
      categories = results[0] as List<ItemWikiCategory>;
      registeredItems = results[1] as List<RegisteredItem>;
      activeItems = results[2] as List<InventoryItem>;
      expiringItems = results[3] as List<InventoryItem>;
      historyItems = results[4] as List<InventoryItem>;
      stats = results[5] as InventoryStats;
    } catch (error) {
      errorMessage = error.toString();
    } finally {
      isLoading = false;
      notifyListeners();
    }
  }

  Future<List<RegisteredItem>> searchRegisteredItems({
    String? categoryId,
    String? keyword,
  }) {
    return repository.getRegisteredItems(categoryId: categoryId, keyword: keyword);
  }

  Future<void> createItem({
    required String name,
    String? categoryId,
    String? description,
    int quantity = 1,
    String? unit,
    DateTime? purchaseDate,
    DateTime? expiryDate,
  }) async {
    await repository.createItem(
      name: name,
      categoryId: categoryId,
      description: description,
      quantity: quantity,
      unit: unit,
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
    );
    await refresh();
  }

  Future<void> updateItemQuantity(String itemId, int delta) async {
    await repository.updateItemQuantity(itemId, delta);
    await refresh();
  }

  Future<void> markAsConsumed(String itemId) async {
    await repository.markAsConsumed(itemId);
    await refresh();
  }

  Future<void> updateItem({
    required String itemId,
    required int quantity,
    String? unit,
    String? description,
    DateTime? purchaseDate,
    DateTime? expiryDate,
    bool isReminderEnabled = true,
  }) async {
    await repository.updateItem(
      itemId: itemId,
      quantity: quantity,
      unit: unit,
      description: description,
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
      isReminderEnabled: isReminderEnabled,
    );
    await refresh();
  }

  Future<void> deleteItem(String itemId) async {
    await repository.deleteItem(itemId);
    await refresh();
  }

  Future<void> restoreItem(String itemId) async {
    await repository.restoreItem(itemId);
    await refresh();
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
    await repository.updateWiki(
      wikiId: wikiId,
      name: name,
      categoryId: categoryId,
      icon: icon,
      description: description,
      defaultUnit: defaultUnit,
      suggestedExpiryDays: suggestedExpiryDays,
      storageLocation: storageLocation,
      notes: notes,
    );
    await refresh();
  }

  Future<void> deleteWiki(String wikiId, {bool force = false}) async {
    await repository.deleteWiki(wikiId, force: force);
    await refresh();
  }

  Future<LegacyImportResult> importLegacyAsset() async {
    final raw = await _loadLegacyImportAsset();
    final payload = jsonDecode(raw) as Map<String, dynamic>;
    final result = await repository.importLegacyData(payload);
    await refresh();
    return result;
  }

  Future<String> _loadLegacyImportAsset() async {
    try {
      return await rootBundle.loadString('assets/import/legacy_inventory.local.json');
    } catch (_) {
      return rootBundle.loadString('assets/import/legacy_inventory.json');
    }
  }
}
