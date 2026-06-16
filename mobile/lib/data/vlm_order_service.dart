import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../models/order_recognition.dart';
import 'vlm_settings_store.dart';

class VlmOrderService {
  VlmOrderService({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  void close() {
    _client.close();
  }

  Future<OrderRecognitionResult> recognizeOrderImage({
    required Uint8List imageBytes,
    required String mimeType,
    required VlmSettings settings,
    List<String> categoryNames = const [],
  }) async {
    if (!settings.isConfigured) {
      throw const OrderRecognitionException(
          '请先在设置里填写 VLM endpoint、model 和 API key');
    }

    final response = await _client.post(
      Uri.parse(settings.endpoint.trim()),
      headers: {
        'Authorization': 'Bearer ${settings.apiKey.trim()}',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'model': settings.model.trim(),
        'temperature': 0.1,
        'max_tokens': 2048,
        'messages': [
          {
            'role': 'system',
            'content': _systemPrompt(categoryNames),
          },
          {
            'role': 'user',
            'content': [
              {
                'type': 'text',
                'text': '识别这张订单截图或购物小票，提取可以加入库存的物品。今天是 ${_todayText()}。',
              },
              {
                'type': 'image_url',
                'image_url': {
                  'url': 'data:$mimeType;base64,${base64Encode(imageBytes)}',
                },
              },
            ],
          },
        ],
      }),
    );

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw OrderRecognitionException(
        'VLM 请求失败：HTTP ${response.statusCode} ${_shortBody(response.body)}',
      );
    }

    final payload =
        jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    final content = _assistantText(payload);
    final json = extractOrderRecognitionJson(content);
    final result = OrderRecognitionResult.fromJson(json);
    if (result.items.isEmpty) {
      throw const OrderRecognitionException('没有识别到可入库的物品');
    }
    return result;
  }
}

class OrderRecognitionException implements Exception {
  const OrderRecognitionException(this.message);

  final String message;

  @override
  String toString() => message;
}

Map<String, dynamic> extractOrderRecognitionJson(String content) {
  final trimmed = content.trim();
  final decoded = _tryDecode(trimmed);
  if (decoded != null) {
    return decoded;
  }

  final fenced = RegExp(r'```(?:json)?\s*([\s\S]*?)```').firstMatch(trimmed);
  if (fenced != null) {
    final fencedDecoded = _tryDecode(fenced.group(1)!.trim());
    if (fencedDecoded != null) {
      return fencedDecoded;
    }
  }

  final start = trimmed.indexOf('{');
  if (start >= 0) {
    var depth = 0;
    var inString = false;
    var escaping = false;
    for (var index = start; index < trimmed.length; index += 1) {
      final char = trimmed[index];
      if (escaping) {
        escaping = false;
        continue;
      }
      if (char == '\\') {
        escaping = true;
        continue;
      }
      if (char == '"') {
        inString = !inString;
        continue;
      }
      if (inString) {
        continue;
      }
      if (char == '{') {
        depth += 1;
      } else if (char == '}') {
        depth -= 1;
        if (depth == 0) {
          final objectText = trimmed.substring(start, index + 1);
          final objectDecoded = _tryDecode(objectText);
          if (objectDecoded != null) {
            return objectDecoded;
          }
        }
      }
    }
  }

  throw const OrderRecognitionException('VLM 返回内容不是可解析的 JSON');
}

Map<String, dynamic>? _tryDecode(String text) {
  try {
    final decoded = jsonDecode(text);
    if (decoded is Map<String, dynamic>) {
      return decoded;
    }
    if (decoded is List) {
      return {'items': decoded};
    }
  } catch (_) {
    return null;
  }
  return null;
}

String _assistantText(Map<String, dynamic> payload) {
  final choices = payload['choices'];
  if (choices is! List || choices.isEmpty) {
    throw const OrderRecognitionException('VLM 返回缺少 choices');
  }
  final first = choices.first;
  if (first is! Map) {
    throw const OrderRecognitionException('VLM 返回 choices 格式无效');
  }
  final message = first['message'];
  if (message is Map) {
    return _contentText(message['content']);
  }
  return _contentText(first['text']);
}

String _contentText(Object? content) {
  if (content is String) {
    return content;
  }
  if (content is List) {
    return content
        .map((part) {
          if (part is String) {
            return part;
          }
          if (part is Map) {
            final text = part['text'] ?? part['content'];
            return text is String ? text : '';
          }
          return '';
        })
        .where((part) => part.isNotEmpty)
        .join('\n');
  }
  throw const OrderRecognitionException('VLM 返回缺少文本内容');
}

String _systemPrompt(List<String> categoryNames) {
  final categories =
      categoryNames.isEmpty ? '食品、日用品、化妆品、药品、其他' : categoryNames.join('、');
  return '''
你是库存应用的订单识别器。只输出 JSON，不要输出 Markdown 或解释。
从订单截图、购物小票、配送清单中提取适合入库的实物商品，忽略运费、优惠券、包装费、会员卡、服务费。
日期使用 yyyy-MM-dd。无法确认的字段填 null，不要凭空编造精确日期。
category_name 尽量从这些分类中选择：$categories。
quantity 必须是正整数；如果截图里是重量或金额，quantity 填 1，并把规格写入 unit 或 notes。
如果截图或商品名明确出现保质期/有效期/到期日，填 expiry_date。
如果只是根据商品常识估算保质期，填 predicted_expiry_date，不要填 expiry_date。
confidence 是 0 到 1 的数字。
输出结构：
{
  "source_app": string | null,
  "merchant": string | null,
  "order_id": string | null,
  "purchase_date": string | null,
  "raw_text": string | null,
  "items": [
    {
      "name": string,
      "quantity": number,
      "unit": string | null,
      "category_name": string | null,
      "purchase_date": string | null,
      "expiry_date": string | null,
      "predicted_expiry_date": string | null,
      "notes": string | null,
      "confidence": number | null
    }
  ]
}
''';
}

String _todayText() {
  final now = DateTime.now();
  return '${now.year.toString().padLeft(4, '0')}-'
      '${now.month.toString().padLeft(2, '0')}-'
      '${now.day.toString().padLeft(2, '0')}';
}

String _shortBody(String body) {
  final text = body.replaceAll(RegExp(r'\s+'), ' ').trim();
  if (text.length <= 160) {
    return text;
  }
  return '${text.substring(0, 160)}...';
}
