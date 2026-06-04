class ItemWikiCategory {
  const ItemWikiCategory({
    required this.id,
    required this.name,
    this.icon,
    this.color,
    required this.sortOrder,
    required this.createdAt,
    required this.updatedAt,
  });

  final String id;
  final String name;
  final String? icon;
  final String? color;
  final int sortOrder;
  final DateTime createdAt;
  final DateTime updatedAt;

  factory ItemWikiCategory.fromMap(Map<String, Object?> map) {
    return ItemWikiCategory(
      id: map['id'] as String,
      name: map['name'] as String,
      icon: map['icon'] as String?,
      color: map['color'] as String?,
      sortOrder: (map['sort_order'] as int?) ?? 0,
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: DateTime.parse(map['updated_at'] as String),
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'name': name,
      'icon': icon,
      'color': color,
      'sort_order': sortOrder,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }
}
