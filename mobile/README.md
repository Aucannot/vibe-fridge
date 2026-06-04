# vibe-fridge Flutter

This directory is the Flutter rewrite of the existing Kivy app. The old Python implementation remains in `../app` while the migration is in progress.

## Current Scope

- Android and macOS target app source.
- SQLite-backed local data layer.
- `Category -> ItemWiki -> Item` domain model preserved from the Python app.
- Home dashboard, item catalog, add item flow, wiki detail, item detail, recipes placeholder, and settings placeholder.
- VLM order screenshot recognition: configure an OpenAI-compatible endpoint in Settings, select an order image from Add, review extracted items, then batch-create inventory records.

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

## VLM Order Recognition

Open Settings and fill:

- Endpoint: defaults to `https://api.siliconflow.cn/v1/chat/completions`.
- Model: defaults to `Qwen/Qwen2.5-VL-72B-Instruct`.
- API Key: stored only in local app preferences.

Then open Add -> `订单截图识别`, choose a receipt/order screenshot, review the recognized items, and confirm import. Recognized items are still created through the same Wiki + inventory path as manual entry.
