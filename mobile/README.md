# vibe-fridge Flutter

This directory is the Flutter rewrite of the existing Kivy app. The old Python implementation remains in `../app` while the migration is in progress.

## Current Scope

- Android and macOS target app source.
- SQLite-backed local data layer.
- `Category -> ItemWiki -> Item` domain model preserved from the Python app.
- Home dashboard, item catalog, add item flow, wiki detail, item detail, recipes placeholder, and settings placeholder.

## Bootstrap

After installing Flutter, run:

```bash
cd mobile
flutter pub get
flutter run -d macos
```

For Android:

```bash
flutter devices
flutter run -d <android-device-id>
```

## Database

The Flutter app creates its own SQLite database through `path_provider` and `sqflite`. It does not mutate the legacy Python database at `../data/vibe_fridge.db`.

To export legacy data into the Flutter import asset:

```bash
cd ..
python tools/export_legacy_inventory.py \
  --source data/vibe_fridge.db \
  --output mobile/assets/import/legacy_inventory.local.json
cd mobile
flutter run -d macos
```

Then open Settings and tap `导入 legacy_inventory.json`. The `.local.json` export is ignored by Git.
