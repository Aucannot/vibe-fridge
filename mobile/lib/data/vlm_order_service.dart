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

  Future<void> validateConfiguration(VlmSettings settings) async {
    _validateSettings(settings);
    final response = await _postChatCompletions(
      settings: settings,
      payload: {
        'model': settings.model.trim(),
        'temperature': 0,
        'max_tokens': 8,
        'messages': const [
          {
            'role': 'user',
            'content': 'ping',
          },
        ],
      },
    );
    _throwForHttpFailure(response);
    try {
      final payload =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      _assistantText(payload);
    } on OrderRecognitionException {
      rethrow;
    } catch (_) {
      throw const OrderRecognitionException(
        '模型返回不可解析，请检查服务地址和模型名称。',
        type: OrderRecognitionErrorType.responseFormat,
      );
    }
  }

  Future<OrderRecognitionResult> recognizeOrderImage({
    required Uint8List imageBytes,
    required String mimeType,
    required VlmSettings settings,
    List<String> categoryNames = const [],
  }) async {
    _validateSettings(settings);

    final response = await _postChatCompletions(
      settings: settings,
      payload: {
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
                'text': [
                  '识别这张订单截图或购物小票。',
                  '提取可以加入库存的物品。',
                  '今天是 ${_todayText()}。',
                ].join(' '),
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
      },
    );

    _throwForHttpFailure(response);

    try {
      final payload =
          jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      final content = _assistantText(payload);
      final json = extractOrderRecognitionJson(content);
      final result = OrderRecognitionResult.fromJson(json);
      if (result.items.isEmpty) {
        throw const OrderRecognitionException(
          '没有识别到可入库的物品',
          type: OrderRecognitionErrorType.responseFormat,
        );
      }
      return result;
    } on OrderRecognitionException {
      rethrow;
    } catch (_) {
      throw const OrderRecognitionException(
        '模型返回不可解析，请在预览前检查模型输出格式。',
        type: OrderRecognitionErrorType.responseFormat,
      );
    }
  }

  Future<http.Response> _postChatCompletions({
    required VlmSettings settings,
    required Map<String, Object?> payload,
  }) async {
    try {
      return await _client.post(
        Uri.parse(settings.endpoint.trim()),
        headers: {
          'Authorization': 'Bearer ${settings.apiKey.trim()}',
          'Content-Type': 'application/json',
        },
        body: jsonEncode(payload),
      );
    } on http.ClientException catch (error) {
      throw OrderRecognitionException(
        '网络错误：${error.message}',
        type: OrderRecognitionErrorType.network,
      );
    } on Exception catch (error) {
      throw OrderRecognitionException(
        '网络错误：$error',
        type: OrderRecognitionErrorType.network,
      );
    }
  }
}

enum OrderRecognitionErrorType {
  configuration,
  network,
  authentication,
  server,
  responseFormat,
  unsupportedImage,
}

class OrderRecognitionException implements Exception {
  const OrderRecognitionException(
    this.message, {
    this.type = OrderRecognitionErrorType.responseFormat,
  });

  final String message;
  final OrderRecognitionErrorType type;

  String get userMessage {
    switch (type) {
      case OrderRecognitionErrorType.configuration:
        return '配置错误：$message';
      case OrderRecognitionErrorType.network:
        return '网络错误：请检查服务地址或网络连接';
      case OrderRecognitionErrorType.authentication:
        return '鉴权失败：请检查 API 密钥';
      case OrderRecognitionErrorType.server:
        return '服务端错误：请检查服务地址和模型名称';
      case OrderRecognitionErrorType.responseFormat:
        return '返回不可解析：请确认当前模型支持订单识别';
      case OrderRecognitionErrorType.unsupportedImage:
        return '图片格式不支持：请换 PNG/JPG/WebP 再试';
    }
  }

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

  throw const OrderRecognitionException(
    '模型返回不可解析，请确认当前模型支持订单识别。',
    type: OrderRecognitionErrorType.responseFormat,
  );
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
    throw const OrderRecognitionException(
      '模型返回不可解析，请检查服务地址和模型名称。',
      type: OrderRecognitionErrorType.responseFormat,
    );
  }
  final first = choices.first;
  if (first is! Map) {
    throw const OrderRecognitionException(
      '模型返回不可解析，请检查服务地址和模型名称。',
      type: OrderRecognitionErrorType.responseFormat,
    );
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
  throw const OrderRecognitionException(
    '模型返回不可解析，请确认当前模型支持订单识别。',
    type: OrderRecognitionErrorType.responseFormat,
  );
}

void _validateSettings(VlmSettings settings) {
  final endpoint = settings.endpoint.trim();
  final uri = Uri.tryParse(endpoint);
  if (endpoint.isEmpty ||
      uri == null ||
      !uri.hasScheme ||
      !uri.hasAuthority ||
      (uri.scheme != 'https' && uri.scheme != 'http')) {
    throw const OrderRecognitionException(
      '服务地址格式无效，请填写完整的 http(s) 地址。',
      type: OrderRecognitionErrorType.configuration,
    );
  }
  if (settings.model.trim().isEmpty) {
    throw const OrderRecognitionException(
      '模型名称不能为空。',
      type: OrderRecognitionErrorType.configuration,
    );
  }
  if (settings.apiKey.trim().isEmpty) {
    throw const OrderRecognitionException(
      'API 密钥未配置或无法从安全存储读取。',
      type: OrderRecognitionErrorType.configuration,
    );
  }
}

void _throwForHttpFailure(http.Response response) {
  if (response.statusCode >= 200 && response.statusCode < 300) {
    return;
  }
  final body = _shortBody(response.body);
  if (response.statusCode == 401 || response.statusCode == 403) {
    throw OrderRecognitionException(
      '鉴权失败：HTTP ${response.statusCode} $body',
      type: OrderRecognitionErrorType.authentication,
    );
  }
  if (response.statusCode == 415 ||
      (response.statusCode == 400 && body.toLowerCase().contains('image'))) {
    throw OrderRecognitionException(
      '图片格式不支持：HTTP ${response.statusCode} $body',
      type: OrderRecognitionErrorType.unsupportedImage,
    );
  }
  throw OrderRecognitionException(
    '服务端错误：HTTP ${response.statusCode} $body',
    type: OrderRecognitionErrorType.server,
  );
}

String _systemPrompt(List<String> categoryNames) {
  final categories =
      categoryNames.isEmpty ? '食品、日用品、化妆品、药品、其他' : categoryNames.join('、');
  return '''
你是库存应用的订单识别器。只输出 JSON，不要输出 Markdown 或解释。
从订单截图、购物小票、配送清单中提取适合入库的实物商品。
优先适配盒马、叮咚买菜、美团、饿了么、京东、淘宝、拼多多、
山姆、Costco 等订单样式。
忽略运费、优惠券、包装费、会员卡、服务费、退款、退货、
取消项和已售后商品。
赠品如果是可入库实物可以保留，但 notes 标明赠品；
无法确认时降低 confidence。
日期使用 yyyy-MM-dd。无法确认的字段填 null，不要凭空编造精确日期。
category_name 尽量从这些分类中选择：$categories。
quantity 必须是正整数。
如果截图里是重量或金额，quantity 填 1，并把规格写入 unit 或 notes。
组合套餐无法可靠拆分时按 1 套入库，并在 notes 写明套餐内容。
如果明确列出了套餐内每个子商品和数量，可以拆成多条 items。
外卖熟食、烘焙、鲜切水果等即食商品，如果无明确到期日，
只填 predicted_expiry_date。
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
