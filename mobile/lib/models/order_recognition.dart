class OrderRecognitionResult {
  const OrderRecognitionResult({
    this.sourceApp,
    this.merchant,
    this.orderId,
    this.purchaseDate,
    this.rawText,
    required this.items,
  });

  final String? sourceApp;
  final String? merchant;
  final String? orderId;
  final DateTime? purchaseDate;
  final String? rawText;
  final List<OrderRecognitionItem> items;

  factory OrderRecognitionResult.fromJson(Map<String, dynamic> json) {
    final items = json['items'];
    return OrderRecognitionResult(
      sourceApp: _text(json['source_app']),
      merchant: _text(json['merchant']),
      orderId: _text(json['order_id']),
      purchaseDate: _date(json['purchase_date']),
      rawText: _text(json['raw_text']),
      items: items is List
          ? items
              .whereType<Map>()
              .map((row) =>
                  OrderRecognitionItem.fromJson(Map<String, dynamic>.from(row)))
              .where((item) => item.name.isNotEmpty)
              .toList()
          : const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'source_app': sourceApp,
      'merchant': merchant,
      'order_id': orderId,
      'purchase_date': _dateText(purchaseDate),
      'raw_text': rawText,
      'items': items.map((item) => item.toJson()).toList(),
    };
  }
}

class OrderRecognitionItem {
  const OrderRecognitionItem({
    required this.name,
    this.quantity = 1,
    this.unit,
    this.categoryName,
    this.purchaseDate,
    this.expiryDate,
    this.predictedExpiryDate,
    this.notes,
    this.confidence,
  });

  final String name;
  final int quantity;
  final String? unit;
  final String? categoryName;
  final DateTime? purchaseDate;
  final DateTime? expiryDate;
  final DateTime? predictedExpiryDate;
  final String? notes;
  final double? confidence;

  DateTime? get inventoryExpiryDate => expiryDate ?? predictedExpiryDate;

  factory OrderRecognitionItem.fromJson(Map<String, dynamic> json) {
    return OrderRecognitionItem(
      name: _text(json['name']) ?? '',
      quantity: _positiveInt(json['quantity']),
      unit: _text(json['unit']),
      categoryName: _text(json['category_name']),
      purchaseDate: _date(json['purchase_date']),
      expiryDate: _date(json['expiry_date']),
      predictedExpiryDate: _date(json['predicted_expiry_date']),
      notes: _text(json['notes']),
      confidence: _confidence(json['confidence']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'quantity': quantity,
      'unit': unit,
      'category_name': categoryName,
      'purchase_date': _dateText(purchaseDate),
      'expiry_date': _dateText(expiryDate),
      'predicted_expiry_date': _dateText(predictedExpiryDate),
      'notes': notes,
      'confidence': confidence,
    };
  }
}

String? _text(Object? value) {
  if (value is! String) {
    return null;
  }
  final trimmed = value.trim();
  return trimmed.isEmpty ? null : trimmed;
}

DateTime? _date(Object? value) {
  final text = _text(value);
  if (text == null) {
    return null;
  }
  final parsed = DateTime.tryParse(text);
  if (parsed == null) {
    return null;
  }
  return DateTime(parsed.year, parsed.month, parsed.day);
}

String? _dateText(DateTime? value) {
  if (value == null) {
    return null;
  }
  return DateTime(value.year, value.month, value.day)
      .toIso8601String()
      .split('T')
      .first;
}

int _positiveInt(Object? value) {
  int? parsed;
  if (value is int) {
    parsed = value;
  } else if (value is num) {
    parsed = value.round();
  } else if (value is String) {
    parsed = int.tryParse(value);
  }
  if (parsed == null || parsed < 1) {
    return 1;
  }
  return parsed;
}

double? _confidence(Object? value) {
  if (value is num) {
    return value.toDouble().clamp(0, 1).toDouble();
  }
  if (value is String) {
    final parsed = double.tryParse(value);
    return parsed?.clamp(0, 1).toDouble();
  }
  return null;
}
