# vibe-fridge Flutter

This directory is the Flutter rewrite of the existing Kivy app. The old Python implementation remains in `../app` while the migration is in progress.

## Current Scope

- Android and macOS target app source.
- SQLite-backed local data layer.
- `Category -> ItemWiki -> Item` domain model preserved from the Python app.
- Home dashboard, item catalog, add item flow, wiki detail, item detail, recipes placeholder, and settings placeholder.

## Bootstrap

Flutter is not installed in the current Codex environment, so the generated Android/macOS platform folders are intentionally not checked in yet. After installing Flutter, run:

```bash
cd mobile
flutter create --platforms=android,macos .
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

The first migration target is data export/import from the existing SQLAlchemy database into the Flutter schema.
