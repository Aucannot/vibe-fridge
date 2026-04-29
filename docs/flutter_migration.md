# Flutter Migration Plan

This repository now contains two app implementations during the migration period:

- `app/`: legacy Python/Kivy implementation.
- `mobile/`: new Flutter implementation targeting Android and macOS.

## Architecture Target

The Flutter app keeps the existing product model:

```text
ItemWikiCategory -> ItemWiki -> InventoryItem
```

`ItemWiki` remains the item class definition. `InventoryItem` is the concrete stock batch. Creating a stock batch automatically creates or updates the matching Wiki entry.

## Implemented in `mobile/`

- Material 3 Flutter app shell.
- Bottom navigation matching the existing Kivy app:
  - 首页
  - 物品
  - 添加
  - 食谱
  - 设置
- Local SQLite database through `sqflite`.
- Default categories and sample Wiki data.
- Home dashboard statistics.
- Item catalog filtered by category/search.
- Add item form.
- Wiki detail page.
- Inventory detail page with quantity updates and consumed marking.

## Database Strategy

The Flutter app creates an independent SQLite database in the platform application support directory. It does not mutate the legacy database at:

```text
data/vibe_fridge.db
```

This avoids accidental data loss while the new app is still being validated.

## Next Migration Steps

1. Install Flutter locally.
2. Generate native platform folders:

   ```bash
   cd mobile
   flutter create --platforms=android,macos .
   ```

3. Fetch packages and run static checks:

   ```bash
   flutter pub get
   flutter analyze
   flutter test
   ```

4. Run macOS:

   ```bash
   flutter run -d macos
   ```

5. Implement legacy data import from `data/vibe_fridge.db`.
6. Add Android notifications and OCR/camera flows after the core inventory loop is stable.

## Current Tooling Limitation

The current Codex environment does not have `flutter` or `dart` on `PATH`, so platform folders and analyzer output are not generated in this pass.
