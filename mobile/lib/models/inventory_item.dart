import 'item_status.dart';

class InventoryItem {
  const InventoryItem({
    required this.id,
    required this.wikiId,
    required this.name,
    this.description,
    required this.quantity,
    this.unit,
    this.purchaseDate,
    this.expiryDate,
    this.reminderDate,
    required this.status,
    required this.isReminderEnabled,
    this.consumedAt,
    this.predictedExpiryDate,
    this.predictionConfidence,
    this.imagePath,
    this.sourceApp,
    this.sourceOrderId,
    required this.createdAt,
    required this.updatedAt,
    this.categoryName,
    this.wikiIcon,
    this.tags = const [],
  });

  final String id;
  final String wikiId;
  final String name;
  final String? description;
  final int quantity;
  final String? unit;
  final DateTime? purchaseDate;
  final DateTime? expiryDate;
  final DateTime? reminderDate;
  final ItemStatus status;
  final bool isReminderEnabled;
  final DateTime? consumedAt;
  final DateTime? predictedExpiryDate;
  final double? predictionConfidence;
  final String? imagePath;
  final String? sourceApp;
  final String? sourceOrderId;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String? categoryName;
  final String? wikiIcon;
  final List<String> tags;

  bool get isExpired {
    final expiry = expiryDate;
    if (expiry == null) {
      return false;
    }
    final today = DateTime.now();
    final dateOnly = DateTime(today.year, today.month, today.day);
    return expiry.isBefore(dateOnly);
  }

  int? get daysUntilExpiry {
    final expiry = expiryDate;
    if (expiry == null) {
      return null;
    }
    final today = DateTime.now();
    final dateOnly = DateTime(today.year, today.month, today.day);
    return expiry.difference(dateOnly).inDays;
  }

  bool get shouldRemind {
    final reminder = reminderDate;
    if (!isReminderEnabled || reminder == null || status != ItemStatus.active) {
      return false;
    }
    final today = DateTime.now();
    final dateOnly = DateTime(today.year, today.month, today.day);
    return !reminder.isAfter(dateOnly);
  }

  factory InventoryItem.fromMap(Map<String, Object?> map) {
    return InventoryItem(
      id: map['id'] as String,
      wikiId: map['wiki_id'] as String,
      name: map['name'] as String,
      description: map['description'] as String?,
      quantity: (map['quantity'] as int?) ?? 1,
      unit: map['unit'] as String?,
      purchaseDate: _dateFromDb(map['purchase_date']),
      expiryDate: _dateFromDb(map['expiry_date']),
      reminderDate: _dateFromDb(map['reminder_date']),
      status: ItemStatus.fromDbValue(map['status'] as String?),
      isReminderEnabled: ((map['is_reminder_enabled'] as int?) ?? 1) == 1,
      consumedAt: _dateTimeFromDb(map['consumed_at']),
      predictedExpiryDate: _dateFromDb(map['predicted_expiry_date']),
      predictionConfidence: (map['prediction_confidence'] as num?)?.toDouble(),
      imagePath: map['image_path'] as String?,
      sourceApp: map['source_app'] as String?,
      sourceOrderId: map['source_order_id'] as String?,
      createdAt: DateTime.parse(map['created_at'] as String),
      updatedAt: DateTime.parse(map['updated_at'] as String),
      categoryName: map['category_name'] as String?,
      wikiIcon: map['wiki_icon'] as String?,
      tags: const [],
    );
  }

  Map<String, Object?> toMap() {
    return {
      'id': id,
      'wiki_id': wikiId,
      'name': name,
      'description': description,
      'quantity': quantity,
      'unit': unit,
      'purchase_date': _dateToDb(purchaseDate),
      'expiry_date': _dateToDb(expiryDate),
      'reminder_date': _dateToDb(reminderDate),
      'status': status.dbValue,
      'is_reminder_enabled': isReminderEnabled ? 1 : 0,
      'consumed_at': consumedAt?.toIso8601String(),
      'predicted_expiry_date': _dateToDb(predictedExpiryDate),
      'prediction_confidence': predictionConfidence,
      'image_path': imagePath,
      'source_app': sourceApp,
      'source_order_id': sourceOrderId,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
    };
  }

  InventoryItem copyWith({
    int? quantity,
    ItemStatus? status,
    DateTime? consumedAt,
  }) {
    return InventoryItem(
      id: id,
      wikiId: wikiId,
      name: name,
      description: description,
      quantity: quantity ?? this.quantity,
      unit: unit,
      purchaseDate: purchaseDate,
      expiryDate: expiryDate,
      reminderDate: reminderDate,
      status: status ?? this.status,
      isReminderEnabled: isReminderEnabled,
      consumedAt: consumedAt ?? this.consumedAt,
      predictedExpiryDate: predictedExpiryDate,
      predictionConfidence: predictionConfidence,
      imagePath: imagePath,
      sourceApp: sourceApp,
      sourceOrderId: sourceOrderId,
      createdAt: createdAt,
      updatedAt: updatedAt,
      categoryName: categoryName,
      wikiIcon: wikiIcon,
      tags: tags,
    );
  }
}

DateTime? _dateFromDb(Object? value) {
  if (value == null) {
    return null;
  }
  return DateTime.parse(value as String);
}

DateTime? _dateTimeFromDb(Object? value) {
  if (value == null) {
    return null;
  }
  return DateTime.parse(value as String);
}

String? _dateToDb(DateTime? value) {
  if (value == null) {
    return null;
  }
  final normalized = DateTime(value.year, value.month, value.day);
  return normalized.toIso8601String();
}
