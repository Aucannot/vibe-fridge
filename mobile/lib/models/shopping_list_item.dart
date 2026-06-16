class ShoppingListItem {
  const ShoppingListItem({
    required this.id,
    required this.name,
    this.categoryId,
    this.categoryName,
    this.sourceWikiId,
    this.sourceItemId,
    required this.quantity,
    this.unit,
    this.note,
    required this.source,
    required this.isChecked,
    this.checkedAt,
    this.convertedAt,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String name;
  final String? categoryId;
  final String? categoryName;
  final String? sourceWikiId;
  final String? sourceItemId;
  final int quantity;
  final String? unit;
  final String? note;
  final String source;
  final bool isChecked;
  final DateTime? checkedAt;
  final DateTime? convertedAt;
  final DateTime createdAt;
  final DateTime updatedAt;

  String get quantityLabel {
    final suffix = unit == null || unit!.isEmpty ? '' : unit!;
    return '$quantity$suffix';
  }

  factory ShoppingListItem.fromMap(Map<String, Object?> map) {
    return ShoppingListItem(
      id: map['id'] as String,
      name: map['name'] as String,
      categoryId: map['category_id'] as String?,
      categoryName: map['category_name'] as String?,
      sourceWikiId: map['source_wiki_id'] as String?,
      sourceItemId: map['source_item_id'] as String?,
      quantity: (map['quantity'] as int?) ?? 1,
      unit: map['unit'] as String?,
      note: map['note'] as String?,
      source: (map['source'] as String?) ?? 'manual',
      isChecked: ((map['is_checked'] as int?) ?? 0) == 1,
      checkedAt: _dateTimeFromDb(map['checked_at']),
      convertedAt: _dateTimeFromDb(map['converted_at']),
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: DateTime.parse(map['updated_at'] as String),
    );
  }
}

class ShoppingListDraft {
  const ShoppingListDraft({
    required this.name,
    this.categoryId,
    this.sourceWikiId,
    this.sourceItemId,
    this.quantity = 1,
    this.unit,
    this.note,
    this.source = 'manual',
  });

  final String name;
  final String? categoryId;
  final String? sourceWikiId;
  final String? sourceItemId;
  final int quantity;
  final String? unit;
  final String? note;
  final String source;
}

class ShoppingSuggestion {
  const ShoppingSuggestion({
    required this.wikiId,
    required this.name,
    this.categoryId,
    this.categoryName,
    this.categoryIcon,
    required this.quantity,
    this.unit,
    required this.reason,
    required this.source,
    required this.priority,
  });

  final String wikiId;
  final String name;
  final String? categoryId;
  final String? categoryName;
  final String? categoryIcon;
  final int quantity;
  final String? unit;
  final String reason;
  final String source;
  final int priority;

  ShoppingListDraft toDraft() {
    return ShoppingListDraft(
      name: name,
      categoryId: categoryId,
      sourceWikiId: wikiId,
      quantity: quantity,
      unit: unit,
      note: reason,
      source: source,
    );
  }

  factory ShoppingSuggestion.fromMap(Map<String, Object?> map) {
    final activeQuantity = (map['active_quantity'] as int?) ?? 0;
    final consumedCount = (map['consumed_count'] as int?) ?? 0;
    final unit = map['default_unit'] as String?;
    final reason = _suggestionReason(
      activeQuantity: activeQuantity,
      consumedCount: consumedCount,
      unit: unit,
    );
    final source = activeQuantity <= 1 ? 'low_stock' : 'frequent';
    return ShoppingSuggestion(
      wikiId: map['wiki_id'] as String,
      name: map['name'] as String,
      categoryId: map['category_id'] as String?,
      categoryName: map['category_name'] as String?,
      categoryIcon: map['category_icon'] as String?,
      quantity: _suggestedQuantity(map['name'] as String, unit),
      unit: unit,
      reason: reason,
      source: source,
      priority: _suggestionPriority(
        activeQuantity: activeQuantity,
        consumedCount: consumedCount,
      ),
    );
  }
}

String _suggestionReason({
  required int activeQuantity,
  required int consumedCount,
  required String? unit,
}) {
  final suffix = unit == null || unit.isEmpty ? '' : unit;
  if (activeQuantity == 0 && consumedCount > 0) {
    return '已用完 · 消耗过 $consumedCount 次';
  }
  if (activeQuantity <= 1) {
    return '低库存 · 还剩 $activeQuantity$suffix';
  }
  return '常买 · 消耗过 $consumedCount 次';
}

int _suggestionPriority({
  required int activeQuantity,
  required int consumedCount,
}) {
  if (activeQuantity == 0 && consumedCount > 0) {
    return 0;
  }
  if (activeQuantity <= 1) {
    return 1;
  }
  return consumedCount >= 2 ? 2 : 3;
}

int _suggestedQuantity(String name, String? unit) {
  if (unit == '个' && name.contains('鸡蛋')) {
    return 12;
  }
  return 1;
}

DateTime? _dateTimeFromDb(Object? value) {
  if (value == null) {
    return null;
  }
  return DateTime.parse(value as String);
}
