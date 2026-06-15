# Warm Lifestyle UI Refresh Goal

Implement a Flutter UI refresh for vibe-fridge using Scheme C · Warm Lifestyle.

Use these design references:

- `docs/ui-drafts/warm-lifestyle-refined.svg`
- `docs/ui-drafts/warm-lifestyle-design-system.svg`

Focus files:

- `mobile/lib/theme/app_theme.dart`
- `mobile/lib/widgets/app_cards.dart`
- `mobile/lib/screens/home_screen.dart`
- `mobile/lib/screens/items_screen.dart`
- `mobile/lib/screens/add_item_screen.dart`
- `mobile/lib/screens/order_import_review_screen.dart`
- `mobile/lib/screens/item_detail_screen.dart`
- `mobile/lib/screens/item_edit_screen.dart`
- `mobile/lib/screens/recipes_screen.dart`
- `mobile/lib/screens/settings_screen.dart`

Keep existing inventory CRUD, order recognition, import review, legacy import, and settings behavior.

Do not build a generic TodoList feature.
Do not replace SQLite or rewrite the app architecture.
Do not add cloud sync or a real AI recipe backend.

Required checks:

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
```
