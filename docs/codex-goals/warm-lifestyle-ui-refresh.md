# Codex Goal: Implement Warm Lifestyle UI refresh for vibe-fridge

## Context

vibe-fridge is a local-first fridge / home inventory app. The current Flutter app works, but the UI needs a full visual refresh.

We selected **Scheme C · Warm Lifestyle** as the visual direction.

Use these design references as the source of truth:

- `docs/ui-drafts/warm-lifestyle-spec.md`
- `docs/ui-drafts/warm-lifestyle-refined.png` when available
- `docs/ui-drafts/warm-lifestyle-design-system.png` when available

The UI direction is:

- Warm, family-friendly, food-first
- Soft cream background
- Sage green primary color
- Olive secondary accents
- Lavender used sparingly for health/freshness/status accents
- Card-based layout
- Rounded corners
- Light shadows
- Clear hierarchy
- Chinese UI copy
- Mobile-first, but still usable on macOS

Do **not** implement a generic TodoList feature. The TODO file is a project roadmap, not an app feature request.

## Current app structure

The Flutter app lives under `mobile/`.

Important files:

- `mobile/lib/main.dart`
- `mobile/lib/theme/app_theme.dart`
- `mobile/lib/widgets/app_cards.dart`
- `mobile/lib/screens/app_shell.dart`
- `mobile/lib/screens/home_screen.dart`
- `mobile/lib/screens/items_screen.dart`
- `mobile/lib/screens/add_item_screen.dart`
- `mobile/lib/screens/order_import_review_screen.dart`
- `mobile/lib/screens/item_detail_screen.dart`
- `mobile/lib/screens/item_edit_screen.dart`
- `mobile/lib/screens/item_wiki_detail_screen.dart`
- `mobile/lib/screens/recipes_screen.dart`
- `mobile/lib/screens/settings_screen.dart`

Prefer evolving existing code instead of replacing the app architecture.

## Phase 1: Design system refresh

Update the shared design system first.

### Tasks

1. Update `AppColors` in `mobile/lib/theme/app_theme.dart` to match Scheme C:
   - warm cream app background
   - sage green primary
   - olive secondary
   - soft lavender accent
   - warm orange warning
   - soft red error
   - card/surface colors
   - text hierarchy colors

2. Update `AppTheme.light()`:
   - Material 3 enabled
   - warm background
   - consistent input style
   - rounded controls
   - consistent chip style
   - bottom navigation style closer to the design draft
   - filled/outlined button styles matching the design system

3. Update shared components in `mobile/lib/widgets/app_cards.dart`:
   - `PageHeader`
   - `SectionCard`
   - `MetricCard`
   - `StatusPill`
   - `EmptyState`
   - `ContentWidth`

4. Add any small reusable components needed for the refreshed UI, for example:
   - warm action tile
   - compact icon tile
   - expiry/freshness card
   - bottom CTA wrapper
   - image placeholder card

### Acceptance criteria

- Existing screens still compile.
- No business logic changes in Phase 1.
- UI has consistent background, cards, chips, buttons, and bottom navigation.
- `flutter analyze` passes.

## Phase 2: Refresh core screens

Refresh these pages to match the Warm Lifestyle direction.

### 2.1 Home dashboard

Update `mobile/lib/screens/home_screen.dart`.

Target layout:

- Greeting header:
  - app name
  - warm greeting copy
  - notification/settings-style icon if useful
  - subtle fridge/plant visual area if easy, but do not require image assets
- “冰箱健康评分” or equivalent summary card
- “即将过期” horizontal cards
- “快捷操作” tiles:
  - 添加物品
  - 扫一扫 / 订单识别
  - 智能菜谱
  - 清理建议
- “今日任务 / 今日要处理” list using existing inventory data
- Bottom navigation preserved

Use existing controller data:

- `stats`
- `expiringItems`
- `activeItems`
- category counts

Do not invent unsupported backend data. Placeholder UI is acceptable only where clearly marked as coming soon.

### 2.2 Inventory list

Update `mobile/lib/screens/items_screen.dart`.

Target layout:

- Search field
- Category chips
- Grouping by freshness/expiry state where practical:
  - 即将过期
  - 冷藏
  - 冷冻
  - 常温
- Item rows with image/icon, name, category/storage, quantity, expiry pill
- History view still available

Do not remove existing search/category/history functionality.

### 2.3 Add item

Update `mobile/lib/screens/add_item_screen.dart`.

Target layout:

- Two prominent scan options at top:
  - 拍照识别（食材/包装）
  - 扫一扫（条码/小票）
- Manual input form below:
  - name
  - category
  - quantity + unit
  - purchase date
  - expiry date
  - storage location if already supported, otherwise show as future placeholder or omit
  - notes
- Primary CTA: 保存

Keep existing order screenshot recognition flow working.

### 2.4 Order recognition preview

Update `mobile/lib/screens/order_import_review_screen.dart`.

Target layout:

- Receipt/image preview at top
- Recognition summary:
  - recognized count
  - needs confirmation count
  - total amount if available
- Editable recognized rows:
  - image/icon
  - name
  - quantity stepper
  - unit
  - confidence/status
  - include/exclude checkbox
- Bottom CTA:
  - 确认入库
- Low confidence items should be visually highlighted

Keep existing import logic working.

### 2.5 Item detail

Update `mobile/lib/screens/item_detail_screen.dart` and `mobile/lib/screens/item_edit_screen.dart`.

Target layout:

- Large item hero card
- Quantity stepper
- Freshness / expiry timeline
- Storage advice card
- Reminder settings card
- Notes
- Actions:
  - edit
  - mark consumed
  - delete
  - restore where applicable

Use existing item fields only. Do not add schema changes unless absolutely necessary.

### 2.6 Recipe screen

Update `mobile/lib/screens/recipes_screen.dart`.

Target layout:

- Replace placeholder screen with warm recipe suggestion UI.
- Use existing inventory data if available. If the screen currently has no controller, minimally wire the existing `InventoryController` into it through `AppShell`.
- Show:
  - “根据库存推荐”
  - recipe cards
  - ingredients available/missing indicator
  - “优先消耗” tags
- If no AI backend exists, implement deterministic placeholder suggestions from expiring items and clearly label as local suggestions.

Do not implement a full AI recipe backend in this goal.

### 2.7 Settings

Update `mobile/lib/screens/settings_screen.dart`.

Target layout:

- Local data card
- VLM settings card
- Notification settings card
- Migration status card
- About card
- Same Warm Lifestyle component style

Keep existing import and VLM settings functionality.

## Phase 3: Small functional improvements allowed

Only implement small improvements directly needed by the UI refresh.

Allowed:

- Pass `InventoryController` into `RecipesScreen` so recipes can use inventory data.
- Add pure UI helper methods/classes.
- Add local deterministic recipe suggestions based on expiring items.
- Add non-persistent computed labels such as freshness state, urgency, storage advice.
- Add better empty/error/loading states.

Not allowed:

- Do not add a generic TodoList feature.
- Do not add a new database table unless required by existing broken functionality.
- Do not migrate app to a new state management framework.
- Do not replace SQLite layer.
- Do not add real cloud sync.
- Do not add a real AI recipe API integration.
- Do not remove legacy import or VLM settings.
- Do not remove existing inventory CRUD behavior.

## Visual implementation notes

Use the design-system draft as guidance:

- Background: warm cream, not pure white.
- Cards: white/cream surfaces with subtle borders and soft shadows.
- Primary button: sage green.
- Secondary button: outlined or soft surface.
- Error/destructive: soft red.
- Warning/expiry: orange.
- Healthy/fresh: sage/olive green.
- Freshness/health accents may use lavender.
- Bottom nav: rounded, warm surface, centered add action if practical.
- Prefer Chinese copy.

## Required final checks

Run:

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
```

If Flutter is not on PATH, try the known local path mentioned in docs:

```bash
/Users/wuhongman/develop/flutter/bin/flutter pub get
/Users/wuhongman/develop/flutter/bin/flutter analyze
/Users/wuhongman/develop/flutter/bin/flutter test
```

## Deliverables

1. Updated Flutter UI matching Scheme C Warm Lifestyle.
2. Existing functionality preserved:
   - dashboard
   - inventory list/search/history
   - add item
   - order screenshot recognition
   - import review
   - item detail/edit/delete/consume/restore
   - settings and VLM config
3. Recipe screen upgraded from placeholder to local inventory-based suggestion UI.
4. `flutter analyze` passes.
5. Tests pass, or document why a test cannot run.
6. PR description includes screenshots of:
   - Home
   - Inventory list
   - Add item
   - Order recognition preview
   - Item detail
   - Recipe screen
   - Settings
