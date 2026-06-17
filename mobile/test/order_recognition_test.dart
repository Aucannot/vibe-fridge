import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vibe_fridge/data/order_text_import_parser.dart';
import 'package:vibe_fridge/data/vlm_order_service.dart';
import 'package:vibe_fridge/data/vlm_settings_store.dart';
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

  test('parses mixed-language order recognition fixture', () {
    final fixture = File(
      'test/fixtures/order_recognition/mixed_order.json',
    ).readAsStringSync();
    final result = OrderRecognitionResult.fromJson(
      jsonDecode(fixture) as Map<String, dynamic>,
    );

    expect(result.sourceApp, 'Hema');
    expect(result.orderId, 'MIXED-ORDER-001');
    expect(result.items, hasLength(4));
    expect(result.items.map((item) => item.name), contains('Organic Milk'));
    expect(
      result.items.map((item) => item.name),
      contains('组合套餐A（苹果+香蕉）'),
    );
    expect(result.items.map((item) => item.name), isNot(contains('退款')));

    final gift = result.items.singleWhere((item) => item.name == '赠品纸巾');
    expect(gift.categoryName, '日用品');
    expect(gift.confidence, lessThan(0.7));
  });

  test('parses pasted order text fallback and skips refund rows', () {
    final result = parseOrderTextImport('''
商家：盒马鲜生
订单号：TEXT-001
购买日期：2026-05-01
Organic Milk x2
组合套餐A（苹果+香蕉） 1套
退款 草莓酸奶 1杯
赠品纸巾 1包
鸡蛋 12枚
香蕉 3根
''');

    expect(result.sourceApp, '手动粘贴');
    expect(result.merchant, '盒马鲜生');
    expect(result.orderId, 'TEXT-001');
    expect(result.purchaseDate, DateTime(2026, 5, 1));
    expect(result.items.map((item) => item.name), contains('Organic Milk'));
    expect(
      result.items.map((item) => item.name),
      contains('组合套餐A（苹果+香蕉）'),
    );
    expect(result.items.map((item) => item.name), isNot(contains('草莓酸奶')));

    final milk = result.items.singleWhere((item) => item.name == 'Organic Milk');
    expect(milk.quantity, 2);

    final gift = result.items.singleWhere((item) => item.name == '赠品纸巾');
    expect(gift.quantity, 1);
    expect(gift.unit, '包');
    expect(gift.categoryName, '日用品');
    expect(gift.confidence, lessThan(0.7));

    final eggs = result.items.singleWhere((item) => item.name == '鸡蛋');
    expect(eggs.quantity, 12);
    expect(eggs.unit, '枚');

    final banana = result.items.singleWhere((item) => item.name == '香蕉');
    expect(banana.quantity, 3);
    expect(banana.unit, '根');
  });

  test('validates VLM configuration successfully', () async {
    final service = VlmOrderService(
      client: MockClient(
        (_) async => http.Response.bytes(
          utf8.encode(
            jsonEncode({
              'choices': [
                {
                  'message': {'content': 'pong'},
                },
              ],
            }),
          ),
          200,
        ),
      ),
    );
    addTearDown(service.close);

    await service.validateConfiguration(_settings());
  });

  test('classifies invalid endpoint configuration', () async {
    final service = VlmOrderService(client: MockClient((_) async {
      return http.Response('{}', 200);
    }));
    addTearDown(service.close);

    expect(
      () => service.validateConfiguration(_settings(endpoint: 'not-a-url')),
      throwsA(
        isA<OrderRecognitionException>().having(
          (error) => error.type,
          'type',
          OrderRecognitionErrorType.configuration,
        ),
      ),
    );
  });

  test('classifies auth failure', () async {
    final service = VlmOrderService(
      client: MockClient((_) async => http.Response('unauthorized', 401)),
    );
    addTearDown(service.close);

    expect(
      () => service.validateConfiguration(_settings()),
      throwsA(
        isA<OrderRecognitionException>().having(
          (error) => error.type,
          'type',
          OrderRecognitionErrorType.authentication,
        ),
      ),
    );
  });

  test('classifies network failure', () async {
    final service = VlmOrderService(
      client: MockClient((_) async => throw http.ClientException('offline')),
    );
    addTearDown(service.close);

    expect(
      () => service.validateConfiguration(_settings()),
      throwsA(
        isA<OrderRecognitionException>().having(
          (error) => error.type,
          'type',
          OrderRecognitionErrorType.network,
        ),
      ),
    );
  });

  test('classifies response format failure', () async {
    final service = VlmOrderService(
      client: MockClient((_) async => http.Response('{"choices":[]}', 200)),
    );
    addTearDown(service.close);

    expect(
      () => service.validateConfiguration(_settings()),
      throwsA(
        isA<OrderRecognitionException>().having(
          (error) => error.type,
          'type',
          OrderRecognitionErrorType.responseFormat,
        ),
      ),
    );
  });
}

VlmSettings _settings({String endpoint = 'https://example.test/v1/chat'}) {
  return VlmSettings(
    endpoint: endpoint,
    model: 'test-model',
    apiKey: 'test-key',
  );
}
