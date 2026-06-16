class ItemWiki {
  const ItemWiki({
    required this.id,
    required this.name,
    this.icon,
    this.description,
    this.categoryId,
    this.categoryName,
    this.defaultUnit,
    this.suggestedExpiryDays,
    required this.defaultReminderDays,
    this.storageLocation,
    this.notes,
    this.imagePath,
    required this.createdAt,
    required this.updatedAt,
    this.inventoryCount = 0,
  });

  final String id;
  final String name;
  final String? icon;
  final String? description;
  final String? categoryId;
  final String? categoryName;
  final String? defaultUnit;
  final int? suggestedExpiryDays;
  final int defaultReminderDays;
  final String? storageLocation;
  final String? notes;
  final String? imagePath;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int inventoryCount;

  factory ItemWiki.fromMap(Map<String, Object?> map) {
    return ItemWiki(
      id: map['id'] as String,
      name: map['name'] as String,
      icon: map['icon'] as String?,
      description: map['description'] as String?,
      categoryId: map['category_id'] as String?,
      categoryName: map['category_name'] as String?,
      defaultUnit: map['default_unit'] as String?,
      suggestedExpiryDays: map['suggested_expiry_days'] as int?,
      defaultReminderDays: (map['default_reminder_days'] as int?) ?? 3,
      storageLocation: map['storage_location'] as String?,
      notes: map['notes'] as String?,
      imagePath: map['image_path'] as String?,
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: DateTime.parse(map['updated_at'] as String),
      inventoryCount: (map['inventory_count'] as int?) ?? 0,
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'name': name,
      'icon': icon,
      'description': description,
      'category_id': categoryId,
      'default_unit': defaultUnit,
      'suggested_expiry_days': suggestedExpiryDays,
      'default_reminder_days': defaultReminderDays,
      'storage_location': storageLocation,
      'notes': notes,
      'image_path': imagePath,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
