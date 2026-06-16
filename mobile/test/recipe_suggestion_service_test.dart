import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/recipe_suggestion_service.dart';
import 'package:vibe_fridge/models/inventory_item.dart';
import 'package:vibe_fridge/models/item_status.dart';

void main() {
  test('sorts priority consumables by expiry then quantity', () {
    final service = RecipeSuggestionService();
    final today = DateTime.now();

    final result = service.priorityConsumables([
      _item('牛奶', quantity: 1, expiryDate: today.add(const Duration(days: 4))),
      _item('鸡蛋', quantity: 12, expiryDate: today.add(const Duration(days: 1))),
      _item('酸奶', quantity: 2, expiryDate: today.add(const Duration(days: 1))),
      _item('洗衣液', categoryName: '日用品'),
    ]);

    expect(result.map((item) => item.name).toList(), [
      '鸡蛋',
      '酸奶',
      '牛奶',
    ]);
  });

  test('generates rule based recipe suggestions from current inventory', () {
    final service = RecipeSuggestionService();
    final today = DateTime.now();

    final suggestions = service.generate([
      _item('鸡蛋', quantity: 12, expiryDate: today.add(const Duration(days: 1))),
      _item('鲜牛奶', expiryDate: today.add(const Duration(days: 2))),
      _item('吐司', expiryDate: today.add(const Duration(days: 3))),
      _item('番茄', expiryDate: today.add(const Duration(days: 1))),
      _item('豆腐', expiryDate: today.add(const Duration(days: 4))),
      _item('米饭', expiryDate: today.add(const Duration(days: 1))),
    ]);

    expect(suggestions.length, greaterThanOrEqualTo(3));
    expect(
      suggestions.map((suggestion) => suggestion.title),
      contains('快手蛋奶早餐'),
    );
    expect(
      suggestions.every((suggestion) => suggestion.inventoryUses.isNotEmpty),
      isTrue,
    );
    expect(
      suggestions.every((suggestion) => suggestion.steps.isNotEmpty),
      isTrue,
    );
  });

  test('keeps fallback recipe suggestions useful for sparse inventory', () {
    final service = RecipeSuggestionService();
    final today = DateTime.now();

    final suggestions = service.generate([
      _item('香蕉', expiryDate: today.add(const Duration(days: 1))),
    ]);

    expect(suggestions, hasLength(3));
    expect(
      suggestions.every((suggestion) => suggestion.inventoryUses.isNotEmpty),
      isTrue,
    );
    expect(
      suggestions.map((suggestion) => suggestion.title),
      containsAll([
        '临期优先拼盘',
        '快手热炒组合',
        '明日便当预处理',
      ]),
    );
  });
}

InventoryItem _item(
  String name, {
  int quantity = 1,
  DateTime? expiryDate,
  String categoryName = '食品',
}) {
  final now = DateTime.now();
  return InventoryItem(
    id: 'item-$name',
    wikiId: 'wiki-$name',
    name: name,
    quantity: quantity,
    unit: '份',
    expiryDate: expiryDate,
    reminderDaysBefore: 3,
    status: ItemStatus.active,
    isReminderEnabled: true,
    createdAt: now,
    updatedAt: now,
    categoryName: categoryName,
  );
}
