class RegisteredItem {
  const RegisteredItem({
    required this.wikiId,
    required this.name,
    this.icon,
    this.categoryId,
    this.categoryName,
    this.description,
    this.defaultUnit,
    this.storageLocation,
    required this.activeBatchCount,
    required this.totalQuantity,
    this.nextExpiryDate,
  });

  final String wikiId;
  final String name;
  final String? icon;
  final String? categoryId;
  final String? categoryName;
  final String? description;
  final String? defaultUnit;
  final String? storageLocation;
  final int activeBatchCount;
  final int totalQuantity;
  final DateTime? nextExpiryDate;

  factory RegisteredItem.fromMap(Map<String, Object?> map) {
    return RegisteredItem(
      wikiId: map['wiki_id'] as String,
      name: map['name'] as String,
      icon: map['icon'] as String?,
      categoryId: map['category_id'] as String?,
      categoryName: map['category_name'] as String?,
      description: map['description'] as String?,
      defaultUnit: map['default_unit'] as String?,
      storageLocation: map['storage_location'] as String?,
      activeBatchCount: (map['active_batch_count'] as int?) ?? 0,
      totalQuantity: (map['total_quantity'] as int?) ?? 0,
      nextExpiryDate: map['next_expiry_date'] == null
          ? null
          : DateTime.parse(map['next_expiry_date'] as String),
    );
  }
}
