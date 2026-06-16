import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:vibe_fridge/data/ai_recipe_service.dart';
import 'package:vibe_fridge/data/recipe_preferences_store.dart';
import 'package:vibe_fridge/data/vlm_settings_store.dart';
import 'package:vibe_fridge/models/inventory_item.dart';
import 'package:vibe_fridge/models/item_status.dart';

void main() {
  test('builds prompt with inventory and user preferences', () {
    final prompt = buildAiRecipePrompt(
      items: [_item('鸡蛋', quantity: 6)],
      preferences: const RecipePreferences(
        flavorProfile: '清淡',
        dietaryRestrictions: '不吃辣',
        cookMinutes: 20,
        servings: 3,
        tools: '电饭煲',
      ),
    );

    expect(prompt, contains('口味：清淡'));
    expect(prompt, contains('忌口/饮食限制：不吃辣'));
    expect(prompt, contains('可用厨具：电饭煲'));
    expect(prompt, contains('人数：3'));
    expect(prompt, contains('inventory_id=item-鸡蛋'));
  });

  test('parses structured AI recipe output and ignores unknown inventory', () {
    final items = [_item('番茄'), _item('鸡蛋', quantity: 3)];
    final suggestions = parseAiRecipeSuggestions(
      inventoryItems: items,
      content: '''
      ```json
      {
        "recipes": [
          {
            "title": "番茄鸡蛋",
            "summary": "优先消耗番茄和鸡蛋。",
            "estimated_minutes": 12,
            "uses": [
              {"inventory_id": "item-番茄", "quantity": 1},
              {"inventory_id": "missing", "quantity": 1},
              {"inventory_id": "item-鸡蛋", "quantity": 5}
            ],
            "missing_ingredients": ["盐"],
            "tags": ["快手"],
            "steps": ["切番茄", "炒鸡蛋"]
          }
        ]
      }
      ```
      ''',
    );

    expect(suggestions, hasLength(1));
    expect(suggestions.single.title, '番茄鸡蛋');
    expect(suggestions.single.tags, containsAll(['AI', '快手']));
    expect(suggestions.single.inventoryUses, hasLength(2));
    expect(suggestions.single.inventoryUses.last.quantity, 3);
  });

  test('returns AI recipes when endpoint responds with valid JSON', () async {
    final service = AiRecipeService(
      client: MockClient((request) async {
        final payload = jsonDecode(request.body) as Map<String, dynamic>;
        expect(payload['model'], 'recipe-model');
        return http.Response(
          jsonEncode({
            'choices': [
              {
                'message': {
                  'content': jsonEncode({
                    'recipes': [
                      {
                        'title': '牛奶燕麦',
                        'summary': '消耗临期牛奶。',
                        'estimated_minutes': 8,
                        'uses': [
                          {'inventory_id': 'item-牛奶', 'quantity': 1},
                        ],
                        'missing_ingredients': ['燕麦'],
                        'tags': ['早餐'],
                        'steps': ['加热牛奶', '拌入燕麦'],
                      },
                    ],
                  }),
                },
              },
            ],
          }),
          200,
          headers: {'content-type': 'application/json; charset=utf-8'},
        );
      }),
    );

    final result = await service.generate(
      items: [_item('牛奶')],
      preferences: const RecipePreferences(),
      settings: const VlmSettings(
        endpoint: 'https://example.com/v1/chat/completions',
        model: 'recipe-model',
        apiKey: 'key',
      ),
    );

    expect(result.usedFallback, isFalse);
    expect(result.suggestions.single.title, '牛奶燕麦');
    service.close();
  });

  test('falls back to rule suggestions when AI configuration is unusable',
      () async {
    final service = AiRecipeService();
    final result = await service.generate(
      items: [
        _item('鸡蛋', quantity: 6),
        _item('牛奶'),
        _item('吐司'),
      ],
      preferences: const RecipePreferences(),
      settings: const VlmSettings(
        endpoint: '',
        model: '',
        apiKey: '',
      ),
    );

    expect(result.usedFallback, isTrue);
    expect(result.suggestions, isNotEmpty);
    expect(result.message, contains('规则建议'));
    service.close();
  });
}

InventoryItem _item(
  String name, {
  int quantity = 1,
  String categoryName = '食品',
}) {
  final now = DateTime.now();
  return InventoryItem(
    id: 'item-$name',
    wikiId: 'wiki-$name',
    name: name,
    quantity: quantity,
    unit: '份',
    expiryDate: now.add(const Duration(days: 2)),
    reminderDaysBefore: 3,
    status: ItemStatus.active,
    isReminderEnabled: true,
    createdAt: now,
    updatedAt: now,
    categoryName: categoryName,
  );
}
