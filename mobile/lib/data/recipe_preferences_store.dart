import 'package:shared_preferences/shared_preferences.dart';

class RecipePreferences {
  const RecipePreferences({
    this.flavorProfile = '',
    this.dietaryRestrictions = '',
    this.cookMinutes = 30,
    this.servings = 2,
    this.tools = '',
  });

  final String flavorProfile;
  final String dietaryRestrictions;
  final int cookMinutes;
  final int servings;
  final String tools;

  RecipePreferences copyWith({
    String? flavorProfile,
    String? dietaryRestrictions,
    int? cookMinutes,
    int? servings,
    String? tools,
  }) {
    return RecipePreferences(
      flavorProfile: flavorProfile ?? this.flavorProfile,
      dietaryRestrictions: dietaryRestrictions ?? this.dietaryRestrictions,
      cookMinutes: cookMinutes ?? this.cookMinutes,
      servings: servings ?? this.servings,
      tools: tools ?? this.tools,
    );
  }
}

class RecipePreferencesStore {
  static const _flavorKey = 'recipe.flavor_profile';
  static const _dietaryKey = 'recipe.dietary_restrictions';
  static const _cookMinutesKey = 'recipe.cook_minutes';
  static const _servingsKey = 'recipe.servings';
  static const _toolsKey = 'recipe.tools';

  Future<RecipePreferences> load() async {
    final preferences = await SharedPreferences.getInstance();
    return RecipePreferences(
      flavorProfile: preferences.getString(_flavorKey) ?? '',
      dietaryRestrictions: preferences.getString(_dietaryKey) ?? '',
      cookMinutes: _boundedInt(
        preferences.getInt(_cookMinutesKey),
        fallback: 30,
        min: 5,
        max: 180,
      ),
      servings: _boundedInt(
        preferences.getInt(_servingsKey),
        fallback: 2,
        min: 1,
        max: 12,
      ),
      tools: preferences.getString(_toolsKey) ?? '',
    );
  }

  Future<void> save(RecipePreferences settings) async {
    final preferences = await SharedPreferences.getInstance();
    await Future.wait([
      preferences.setString(_flavorKey, settings.flavorProfile.trim()),
      preferences.setString(_dietaryKey, settings.dietaryRestrictions.trim()),
      preferences.setInt(
        _cookMinutesKey,
        _boundedInt(settings.cookMinutes, fallback: 30, min: 5, max: 180),
      ),
      preferences.setInt(
        _servingsKey,
        _boundedInt(settings.servings, fallback: 2, min: 1, max: 12),
      ),
      preferences.setString(_toolsKey, settings.tools.trim()),
    ]);
  }
}

int _boundedInt(
  int? value, {
  required int fallback,
  required int min,
  required int max,
}) {
  final actual = value ?? fallback;
  if (actual < min) {
    return min;
  }
  if (actual > max) {
    return max;
  }
  return actual;
}
