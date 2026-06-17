import 'dart:convert';

import 'package:http/http.dart' as http;

import '../models/inventory_item.dart';
import '../models/recipe_suggestion.dart';
import 'recipe_preferences_store.dart';
import 'recipe_suggestion_service.dart';
import 'vlm_settings_store.dart';

class AiRecipeService {
  AiRecipeService({
    http.Client? client,
    RecipeSuggestionService? fallbackService,
  })  : _client = client ?? http.Client(),
        _fallbackService = fallbackService ?? RecipeSuggestionService();

  final http.Client _client;
  final RecipeSuggestionService _fallbackService;

  void close() {
    _client.close();
  }

  Future<AiRecipeGenerationResult> generate({
    required List<InventoryItem> items,
    required RecipePreferences preferences,
    required VlmSettings settings,
  }) async {
    final fallback = _fallbackService.generate(items);
    if (!_hasUsableSettings(settings)) {
      return AiRecipeGenerationResult.fallback(
        suggestions: fallback,
        message: 'AI 食谱未配置，已使用规则建议',
      );
    }

    try {
      final response = await _client.post(
        Uri.parse(settings.endpoint.trim()),
        headers: {
          'Authorization': 'Bearer ${settings.apiKey.trim()}',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'model': settings.model.trim(),
          'temperature': 0.35,
          'max_tokens': 1800,
          'messages': [
            {
              'role': 'system',
              'content': buildAiRecipePrompt(
                items: items,
                preferences: preferences,
              ),
            },
            {
              'role': 'user',
              'content': '请基于当前库存生成 3 到 5 个食谱建议。',
            },
          ],
        }),
      );
      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw AiRecipeException('HTTP ${response.statusCode}');
      }
      final payload = jsonDecode(response.body) as Map<String, dynamic>;
      final content = _assistantText(payload);
      final recipes = parseAiRecipeSuggestions(
        content: content,
        inventoryItems: items,
      );
      if (recipes.isEmpty) {
        throw const AiRecipeException('AI 没有返回可用食谱');
      }
      return AiRecipeGenerationResult.ai(
        suggestions: recipes.take(5).toList(),
      );
    } catch (error) {
      return AiRecipeGenerationResult.fallback(
        suggestions: fallback,
        message: 'AI 食谱暂时不可用，已使用规则建议',
      );
    }
  }
}

class AiRecipeGenerationResult {
  const AiRecipeGenerationResult({
    required this.suggestions,
    required this.usedFallback,
    this.message,
  });

  factory AiRecipeGenerationResult.ai({
    required List<RecipeSuggestion> suggestions,
  }) {
    return AiRecipeGenerationResult(
      suggestions: suggestions,
      usedFallback: false,
    );
  }

  factory AiRecipeGenerationResult.fallback({
    required List<RecipeSuggestion> suggestions,
    required String message,
  }) {
    return AiRecipeGenerationResult(
      suggestions: suggestions,
      usedFallback: true,
      message: message,
    );
  }

  final List<RecipeSuggestion> suggestions;
  final bool usedFallback;
  final String? message;
}

class AiRecipeException implements Exception {
  const AiRecipeException(this.message);

  final String message;

  @override
  String toString() => message;
}

String buildAiRecipePrompt({
  required List<InventoryItem> items,
  required RecipePreferences preferences,
}) {
  final priority = RecipeSuggestionService()
      .priorityConsumables(items)
      .take(12)
      .map(_inventoryPromptLine)
      .join('\n');
  final inventoryText = priority.isEmpty ? '当前没有食品库存。' : priority;
  return '''
你是 vibe-fridge 的库存消耗食谱助手。只输出 JSON，不要输出 Markdown 或解释。
目标：优先消耗临期、已开封、易浪费、数量较多的库存，减少浪费。
今天是 ${_dateText(DateTime.now())}。

用户偏好：
- 口味：${_valueOrDefault(preferences.flavorProfile, '不限')}
- 忌口/饮食限制：${_valueOrDefault(preferences.dietaryRestrictions, '无')}
- 可用厨具：${_valueOrDefault(preferences.tools, '家常锅具')}
- 人数：${preferences.servings}
- 期望烹饪时间：${preferences.cookMinutes} 分钟内

库存候选：
$inventoryText

规则：
1. 生成 3 到 5 个 recipe。
2. uses 只能引用库存候选里的 inventory_id，不要编造库存 id。
3. 每个 recipe 至少使用 1 个库存，优先使用 2 到 4 个。
4. quantity 必须是正整数，不能超过库存 quantity。
5. missing_ingredients 只写用户可能需要额外准备的调味料或主食。
6. estimated_minutes 尽量不超过用户期望时间；确需超过时最多 1 个方案。
7. 避开用户忌口，步骤适合家庭厨房。

输出结构：
{
  "recipes": [
    {
      "title": string,
      "summary": string,
      "estimated_minutes": number,
      "uses": [
        {"inventory_id": string, "quantity": number}
      ],
      "missing_ingredients": [string],
      "tags": [string],
      "steps": [string]
    }
  ]
}
''';
}

List<RecipeSuggestion> parseAiRecipeSuggestions({
  required String content,
  required List<InventoryItem> inventoryItems,
}) {
  final payload = extractAiRecipeJson(content);
  final recipes = payload['recipes'];
  if (recipes is! List) {
    throw const AiRecipeException('AI 食谱缺少 recipes');
  }
  final inventoryById = {
    for (final item in inventoryItems) item.id: item,
  };
  final parsed = <RecipeSuggestion>[];
  for (final row in recipes.whereType<Map>()) {
    final suggestion = _parseSuggestionRow(row, inventoryById, parsed.length);
    if (suggestion != null) {
      parsed.add(suggestion);
    }
  }
  return parsed;
}

Map<String, dynamic> extractAiRecipeJson(String content) {
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

  throw const AiRecipeException('AI 返回内容不是可解析 JSON');
}

RecipeSuggestion? _parseSuggestionRow(
  Map<dynamic, dynamic> row,
  Map<String, InventoryItem> inventoryById,
  int index,
) {
  final title = _text(row['title']);
  final summary = _text(row['summary']);
  final steps = _stringList(row['steps']).take(6).toList();
  final uses = _parseUses(row['uses'], inventoryById);
  if (title == null || summary == null || steps.isEmpty || uses.isEmpty) {
    return null;
  }
  return RecipeSuggestion(
    id: 'ai-recipe-${_slug(title)}-$index',
    title: title,
    summary: summary,
    estimatedMinutes: _positiveInt(row['estimated_minutes'], fallback: 30),
    inventoryUses: uses,
    missingIngredients:
        _stringList(row['missing_ingredients']).take(8).toList(),
    tags: ['AI', ..._stringList(row['tags']).take(4)],
    steps: steps,
  );
}

List<RecipeInventoryUse> _parseUses(
  Object? value,
  Map<String, InventoryItem> inventoryById,
) {
  if (value is! List) {
    return const [];
  }
  final uses = <RecipeInventoryUse>[];
  final seen = <String>{};
  for (final row in value.whereType<Map>()) {
    final id = _text(row['inventory_id']);
    if (id == null || seen.contains(id)) {
      continue;
    }
    final item = inventoryById[id];
    if (item == null) {
      continue;
    }
    seen.add(id);
    final quantity = _positiveInt(row['quantity'], fallback: 1);
    uses.add(
      RecipeInventoryUse(
        item: item,
        quantity: quantity > item.quantity ? item.quantity : quantity,
      ),
    );
  }
  return uses;
}

String _inventoryPromptLine(InventoryItem item) {
  final days = item.daysUntilExpiry;
  final expiry = days == null
      ? '无到期日'
      : days < 0
          ? '已过期 ${days.abs()} 天'
          : '$days 天后到期';
  final tags = item.tags.isEmpty ? '无标签' : item.tags.join('、');
  return [
    '- inventory_id=${item.id}',
    'name=${item.name}',
    'quantity=${item.quantity}${item.unit ?? ''}',
    'category=${item.categoryName ?? '未分类'}',
    'expiry=$expiry',
    'storage=${item.storageLocation ?? '未设置'}',
    'tags=$tags',
  ].join('; ');
}

String _assistantText(Map<String, dynamic> payload) {
  final choices = payload['choices'];
  if (choices is! List || choices.isEmpty) {
    throw const AiRecipeException('AI 返回缺少 choices');
  }
  final first = choices.first;
  if (first is! Map) {
    throw const AiRecipeException('AI 返回 choices 格式无效');
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
  throw const AiRecipeException('AI 返回缺少文本内容');
}

Map<String, dynamic>? _tryDecode(String text) {
  try {
    final decoded = jsonDecode(text);
    if (decoded is Map<String, dynamic>) {
      return decoded;
    }
    if (decoded is List) {
      return {'recipes': decoded};
    }
  } catch (_) {
    return null;
  }
  return null;
}

List<String> _stringList(Object? value) {
  if (value is! List) {
    return const [];
  }
  return value
      .whereType<String>()
      .map((text) => text.trim())
      .where((text) => text.isNotEmpty)
      .toList();
}

String? _text(Object? value) {
  if (value is! String) {
    return null;
  }
  final trimmed = value.trim();
  return trimmed.isEmpty ? null : trimmed;
}

int _positiveInt(Object? value, {required int fallback}) {
  if (value is int && value > 0) {
    return value;
  }
  if (value is num && value > 0) {
    return value.round();
  }
  return fallback;
}

bool _hasUsableSettings(VlmSettings settings) {
  final endpoint = settings.endpoint.trim();
  final uri = Uri.tryParse(endpoint);
  return uri != null &&
      uri.hasScheme &&
      uri.hasAuthority &&
      settings.model.trim().isNotEmpty &&
      settings.apiKey.trim().isNotEmpty;
}

String _valueOrDefault(String value, String fallback) {
  final trimmed = value.trim();
  return trimmed.isEmpty ? fallback : trimmed;
}

String _dateText(DateTime value) {
  final month = value.month.toString().padLeft(2, '0');
  final day = value.day.toString().padLeft(2, '0');
  return '${value.year}-$month-$day';
}

String _slug(String value) {
  final text = value
      .toLowerCase()
      .replaceAll(RegExp(r'[^a-z0-9\u4e00-\u9fa5]+'), '-')
      .replaceAll(RegExp(r'^-+|-+$'), '');
  return text.isEmpty ? 'suggestion' : text;
}
