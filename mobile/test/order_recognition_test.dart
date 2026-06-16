import 'package:flutter_test/flutter_test.dart';
import 'package:vibe_fridge/data/vlm_order_service.dart';
import 'package:vibe_fridge/models/order_recognition.dart';

void main() {
  test('parses fenced VLM JSON into order recognition result', () {
    final payload = extractOrderRecognitionJson('''
```json
{
  "source_app": "盒马",
  "merchant": "盒马鲜生",
  "order_id": "A123",
  "purchase_date": "2026-04-29",
  "items": [
    {
      "name": "鲜牛奶",
      "quantity": 2,
      "unit": "盒",
      "category_name": "食品",
      "expiry_date": null,
      "predicted_expiry_date": "2026-05-06",
      "confidence": 0.91
    }
  ]
}
```
''');

    final result = OrderRecognitionResult.fromJson(payload);

    expect(result.sourceApp, '盒马');
    expect(result.orderId, 'A123');
    expect(result.items, hasLength(1));
    expect(result.items.first.name, '鲜牛奶');
    expect(result.items.first.quantity, 2);
    expect(result.items.first.predictedExpiryDate, DateTime(2026, 5, 6));
    expect(result.items.first.inventoryExpiryDate, DateTime(2026, 5, 6));
  });

  test('wraps array VLM output as items list', () {
    final payload = extractOrderRecognitionJson('''
[
  {"name": "鸡蛋", "quantity": "12", "unit": "个"}
]
''');

    final result = OrderRecognitionResult.fromJson(payload);

    expect(result.items, hasLength(1));
    expect(result.items.first.name, '鸡蛋');
    expect(result.items.first.quantity, 12);
  });
}
