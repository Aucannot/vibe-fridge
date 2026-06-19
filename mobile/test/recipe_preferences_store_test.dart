import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:vibe_fridge/data/recipe_preferences_store.dart';

void main() {
  test('fresh recipe preferences load defaults', () async {
    SharedPreferences.setMockInitialValues({});
    final store = RecipePreferencesStore();

    final loaded = await store.load();

    expect(loaded.flavorProfile, isEmpty);
    expect(loaded.dietaryRestrictions, isEmpty);
    expect(loaded.tools, isEmpty);
    expect(loaded.cookMinutes, 30);
    expect(loaded.servings, 2);
  });

  test('save trims text and bounds numeric preferences', () async {
    SharedPreferences.setMockInitialValues({});
    final store = RecipePreferencesStore();

    await store.save(
      const RecipePreferences(
        flavorProfile: '  清淡少油  ',
        dietaryRestrictions: '  不吃辣  ',
        tools: '  电饭煲  ',
        cookMinutes: 999,
        servings: 0,
      ),
    );

    final loaded = await store.load();

    expect(loaded.flavorProfile, '清淡少油');
    expect(loaded.dietaryRestrictions, '不吃辣');
    expect(loaded.tools, '电饭煲');
    expect(loaded.cookMinutes, 180);
    expect(loaded.servings, 1);
  });

  test('load bounds damaged numeric preferences', () async {
    SharedPreferences.setMockInitialValues({
      'recipe.cook_minutes': 1,
      'recipe.servings': 99,
    });
    final store = RecipePreferencesStore();

    final loaded = await store.load();

    expect(loaded.cookMinutes, 5);
    expect(loaded.servings, 12);
  });
}
