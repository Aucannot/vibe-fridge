import 'inventory_item.dart';

class RecipeSuggestion {
  const RecipeSuggestion({
    required this.id,
    required this.title,
    required this.summary,
    required this.estimatedMinutes,
    required this.inventoryUses,
    required this.missingIngredients,
    required this.steps,
    this.tags = const [],
  });

  final String id;
  final String title;
  final String summary;
  final int estimatedMinutes;
  final List<RecipeInventoryUse> inventoryUses;
  final List<String> missingIngredients;
  final List<String> steps;
  final List<String> tags;

  int get expiringUseCount {
    return inventoryUses.where((use) {
      final days = use.item.daysUntilExpiry;
      return days != null && days <= 3;
    }).length;
  }
}

class RecipeInventoryUse {
  const RecipeInventoryUse({
    required this.item,
    this.quantity = 1,
  });

  final InventoryItem item;
  final int quantity;

  String get quantityText {
    return '$quantity${item.unit ?? ''}';
  }
}
