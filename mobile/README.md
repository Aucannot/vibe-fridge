# vibe-fridge Flutter

This directory is the Flutter rewrite of the existing Kivy app. The old Python implementation remains in `../app` while the migration is in progress.

## Current Scope

- Android and macOS target app source.
- SQLite-backed local data layer.
- `Category -> ItemWiki -> Item` domain model preserved from the Python app.
- Home dashboard, item catalog, shopping list, add item flow, wiki detail, item detail, rule-based recipes, and settings.
- Order recognition: configure an OpenAI-compatible VLM endpoint in Settings, select an order image or paste order text from Add, review extracted items, then batch-create inventory records.

## Bootstrap

After installing Flutter, run from the repository root:

```bash
export PATH="$PWD/.tools/flutter/bin:$PATH"
cd mobile
which flutter
flutter --version
flutter pub get
flutter analyze
flutter test
flutter run -d macos
```

For Android:

```bash
flutter devices
flutter run -d <android-device-id>
```

For local startup on a machine without full Xcode or Android SDK, use the Web
target:

```bash
flutter pub get
flutter build web --debug --no-wasm-dry-run
python3 -m http.server 54324 --bind 127.0.0.1 --directory build/web
```

Open `http://127.0.0.1:54324/`. The checked-in `web/sqlite3.wasm` and
`web/sqflite_sw.js` files back SQLite on Web; if `web/` is regenerated, run
`dart run sqflite_common_ffi_web:setup` before building.

If Flutter is not available on the current machine, the SQLite query smoke
check can still verify that dashboard statistics, today-action reminders, and
catalog search stay responsive with thousands of local records:

```bash
cd mobile
python3 tools/perf_inventory_sqlite.py
```

For Android release builds, copy `android/key.properties.example` to
`android/key.properties` and point `storeFile` at a local upload keystore. The
real `key.properties` and keystore files are ignored by Git. Without that file,
the release build keeps Flutter's debug signing fallback for local smoke tests;
with it, `flutter build apk --release` or `flutter build appbundle --release`
uses the configured release signing key.

Launcher icons are checked in for Android mipmap densities and macOS AppIcon
sizes. The source 1024px brand image lives at `assets/brand/app_icon.png`.
Android startup uses a warm launch background and the same icon through
`launch_background.xml`; Android 12+ uses the v31 splash theme.

For macOS distribution, keep certificates and Apple credentials outside the
repository. Use `flutter build macos --release` for a local release bundle, then
archive and export with Xcode:

```bash
cd mobile
flutter build macos --release
xcodebuild \
  -workspace macos/Runner.xcworkspace \
  -scheme Runner \
  -configuration Release \
  -archivePath build/macos/archive/vibe-fridge.xcarchive \
  DEVELOPMENT_TEAM=<APPLE_TEAM_ID> \
  archive
cp macos/ExportOptions.plist.example /tmp/vibe-fridge-ExportOptions.plist
# Edit /tmp/vibe-fridge-ExportOptions.plist teamID/method for the target channel.
xcodebuild \
  -exportArchive \
  -archivePath build/macos/archive/vibe-fridge.xcarchive \
  -exportOptionsPlist /tmp/vibe-fridge-ExportOptions.plist \
  -exportPath build/macos/export
```

For Developer ID distribution, submit the exported app or zip for notarization
with `xcrun notarytool submit`, then run `xcrun stapler staple` on the exported
app before packaging.

## Platform permissions and privacy

Android declares camera, image-library, notification, and network permissions
in `android/app/src/main/AndroidManifest.xml`. Camera hardware is optional, so
devices without a camera can still install and use manual/file import flows.

macOS declares camera and photo-library purpose strings in
`macos/Runner/Info.plist`, and sandbox entitlements allow user-selected file
reads, selected picture reads, camera access, and outbound network calls.

Local inventory, Wiki, tags, backup metadata, recipe preferences, and VLM
settings stay on the device. API keys are stored with `flutter_secure_storage`.
The app sends order screenshots, pasted order text, and inventory context to a
network service only when the user explicitly runs a configured VLM or AI recipe
action. The endpoint and model are supplied by the user in Settings.

### Network privacy audit

Runtime HTTP usage is intentionally narrow. A source scan for
`package:http`, `http.Client`, `Uri.parse`, and `.post(` shows only these app
services performing outbound requests:

- `lib/data/vlm_order_service.dart`: sends a settings-test ping from Settings
  or an order image/text recognition request from Add after the user starts
  order recognition.
- `lib/data/ai_recipe_service.dart`: sends the prioritized inventory context
  only after the user taps the AI recipe generation action. If endpoint, model,
  or API key are missing, it returns local rule-based suggestions instead.

The home dashboard, item catalog, local recipe rules, shopping list, backup,
legacy import, data-health checks, and in-app acceptance runner do not perform
network calls. The acceptance runner exercises the AI recipe fallback with an
empty `VlmSettings`, so it also stays local.

## Reliability

If SQLite or local data initialization fails during startup, the app shows a
minimal recovery screen instead of a blank window. The screen includes the error
and stack trace as selectable text plus a `复制错误详情` action for issue reports.

Destructive or high-impact actions ask for confirmation before writing: single
and batch inventory deletion, single and batch consume, order batch import,
shopping-list deletion, and checked shopping-list conversion back into inventory.

Debug builds show a `重置示例数据` action in Settings. It clears only the
built-in demo Wiki/inventory ids and seeds them again, leaving user-created data
untouched. The action is hidden outside debug mode.

## Database

The Flutter app creates its own SQLite database through `path_provider` and `sqflite`. It does not mutate the legacy Python database at `../data/vibe_fridge.db`.

Schema changes are handled through `AppDatabase.schemaVersion` and explicit migrations in `lib/data/app_database.dart`. The current schema is version 4:

- v1: baseline Category -> ItemWiki -> Item tables plus tags and reminder logs.
- v2: reserved fields for default reminder rules, item storage location, import batches, recognition confidence, app metadata, and backup snapshots.
- v3: shopping list items for replenishment suggestions, checked purchases, and conversion back into inventory.
- v4: query-performance indexes for dashboard statistics, today-action reminders, catalog category filters, and reminder-log deduplication.

Migration coverage lives in `test/app_database_migration_test.dart`.

The repository also exposes backup and health-check primitives:

- `InventoryRepository.exportBackup()` returns a full JSON-ready backup payload.
- `InventoryRepository.exportInventoryCsv()` returns a human-readable inventory CSV.
- `InventoryRepository.createBackupSnapshot()` stores a local snapshot before risky operations.
- `InventoryRepository.restoreBackup()` restores a backup in a transaction and rolls back if health checks fail.
- `InventoryRepository.checkDataHealth()` validates quantity, status, date format, reminder order, foreign keys, and consumed/active state consistency.

Settings exposes the same backup primitives as file actions: export backup JSON, restore backup JSON, and export inventory CSV. Restoring a backup creates a pre-restore snapshot before replacing local inventory data.

Settings also shows a local backup reminder after the first legacy import or after a large batch of local changes. Exporting a backup JSON clears the reminder and records the latest export time in app metadata.

To export legacy data into the Flutter import asset:

```bash
cd ..
python tools/export_legacy_inventory.py \
  --source data/vibe_fridge.db \
  --output mobile/assets/import/legacy_inventory.local.json
cd mobile
flutter run -d macos
```

Then open Settings and tap `预览并导入 legacy_inventory.json`. The preview shows incoming Category, Wiki, inventory, tag, and item-tag counts plus conflict decisions by id, name, and timestamp. Confirming the dialog runs the import, records success/skip/failure logs, and runs a data-health check afterward. For real migrations, the dialog can clear the built-in demo Wiki/inventory rows before importing. The `.local.json` export is ignored by Git.

## In-app Acceptance Checks

Open Settings and tap `运行自验收`. The app creates a temporary inventory record and verifies the core loop:

- create inventory and auto-link Wiki
- persist storage location, image attachment path, and item tags
- include a 3-day expiry reminder in the `今天要处理` dashboard module
- generate a local-notification payload for reminder-due inventory
- deduplicate same-day reminder logs and hide ignored reminders
- update quantity
- batch-update storage location and Wiki category
- mark one unit as consumed
- restore the consumed record
- delete the restored record
- clean up temporary Wiki/inventory data
- pass the repository data-health check
- generate a rule-based recipe suggestion from active inventory
- create a shopping list item, mark it bought, and convert it back into inventory

The same runner is covered by `test/inventory_repository_test.dart`.

## Expiry Reminders

Each inventory record can enable or disable reminders and set its own `提前天数` in the edit screen. Wiki entries also have a default reminder lead time, used when new inventory batches are created without an item-specific override.

The home dashboard includes `今天要处理`, which aggregates active items that are expired, expire today, or have a reminder date due today or earlier. Platform notifications are still tracked separately in `TODO.md`.

Items in `今天要处理` support `稍后` and `忽略`. Both actions write to `reminder_logs` and hide that item from the section for the current day. `InventoryRepository.recordReminderSentIfNeeded()` also uses the same log table to avoid sending the same item/reminder type more than once per day.

Native local notification wiring is implemented through
`vibe_fridge/local_notifications` without adding a third-party plugin. Settings
can request notification permission and sync upcoming inventory reminders.
Android uses `POST_NOTIFICATIONS`, `AlarmManager`, and a private broadcast
receiver; macOS uses `UNUserNotificationCenter`. Notification taps return the
inventory `itemId` to Flutter and open the inventory detail screen. This still
needs device/build verification once Flutter is available locally.

## Storage Locations

Manual inventory creation and inventory editing support common storage locations: `冷藏`, `冷冻`, `常温`, `药箱`, `浴室`, and `其他`. The selected location is stored on the inventory batch and shown on the detail page.

## Batch Policy

Items with the same name and expiry date share the same Wiki entry but are not automatically merged. Each create action stores a separate inventory batch so package photos, source orders, tags, locations, and later edits remain traceable. Users can adjust quantity on a specific batch or mark units consumed from that batch.

## Batch Operations

Open a Wiki detail page and use `批量` in the inventory batch section, or long-press a batch, to select multiple records. Selected batches can be deleted, moved to a storage location, moved to another Wiki category, or marked as consumed. Batch consume follows the single-item behavior: each selected active batch consumes one unit; batches with quantity greater than one keep the remaining quantity active.

## Image Attachments

Manual inventory creation and inventory editing can attach a package, receipt, or label image from album, file picker, or camera. The selected image is copied into the app documents directory under `attachments/inventory/`, and the detail page shows a local preview plus the saved path.

Order image imports also copy the selected source image into `attachments/order_imports/` before the recognition result is reviewed, so imported inventory keeps a stable local image reference.

## Inventory Tags

Manual inventory creation and inventory editing support preset tags: `临期优先`, `已开封`, `囤货`, `常用`, and `易浪费`. Tags are stored through the local `tags` and `item_tags` tables, shown on the inventory detail page, and covered by the in-app acceptance runner.

## Shopping List

Open `物品` -> `采购` to review replenishment suggestions and the active shopping list. Suggestions are generated locally from low-stock, consumed, and frequently consumed Wiki entries. Items already on the shopping list are not suggested again.

Catalog and history rows include a shopping-cart action for manually adding inventory entries to the list. The list supports checked state, quantity, unit, notes, category grouping, edit/delete actions, and `入库` for checked items. Conversion creates normal inventory records through the same Wiki-aware repository path as manual add.

## Rule-based Recipes

Open `食谱` to see priority consumables sorted by expiry date, quantity, and category. The app then generates 3-5 local rule-based recipe suggestions from active food inventory.

Recipe detail pages show inventory to consume, missing pantry ingredients, steps, estimated time, and expiring item coverage. Tapping `做这道菜并扣减库存` applies the same inventory quantity update path as the detail page. Favorites and recently opened recipes are kept for the current app session.

The same page can request AI recipes through the configured VLM chat-completions endpoint. Recipe preferences live in Settings and cover flavor, dietary restrictions, cookware, servings, and target cooking time. AI output must reference existing inventory ids and is parsed into the same editable `RecipeSuggestion` model; if configuration, network, or response parsing fails, the app falls back to local rule-based suggestions.

## VLM Order Recognition

Open Settings and fill:

- Endpoint: defaults to `https://api.siliconflow.cn/v1/chat/completions`.
- Model: defaults to `Qwen/Qwen2.5-VL-72B-Instruct`.
- API Key: stored in platform secure storage and never written to SharedPreferences.

Use `测试配置` to verify endpoint, model, and key before importing. The settings card also supports clearing all VLM configuration or restoring the default endpoint/model while clearing the saved key.

Then open Add -> `订单识别`, import an image from album, file picker, or camera, or paste order text, review the recognized items, and confirm import.

Camera capture is available through `image_picker` on mobile platforms. On desktop platforms where no system camera picker is available, the app keeps the camera action visible but falls back to a clear prompt to use album/file import.

The review screen supports:

- per-item edits for name, quantity, unit, category, purchase date, predicted expiry date, and confidence
- low-confidence highlighting until the row is confirmed
- duplicate skipping for the same order/product/purchase date
- an import summary with added, skipped, and manually handled counts

Recognized items are still created through the same Wiki + inventory path as manual entry. The inventory detail page shows the source app, order id, import batch, recognition confidence, and original image path when present. VLM errors are classified as configuration, network, authentication, unsupported image format, server, or response-format failures.

The VLM prompt is tuned for common grocery, delivery, and e-commerce screenshots such as Hema, Dingdong, Meituan, Ele.me, JD, Taobao, Pinduoduo, Sam's, and Costco. Refunds and cancelled rows are ignored; gifts and bundles are kept only when they can become inventory records and are flagged for review when confidence is low.

Order recognition fixtures live under `test/fixtures/order_recognition/`. The fallback parser used by `粘贴文本` is covered in `test/order_recognition_test.dart`.

## Troubleshooting

- `flutter: command not found`: install Flutter and add `<flutter-sdk>/bin` to PATH.
- macOS target missing: run `flutter config --enable-macos-desktop`.
- Android target missing: install Android SDK, start an emulator or connect a device, then run `flutter devices`.
- Full Xcode or Android SDK unavailable: use the Web startup path above for local launch verification.
- Dependency drift: run `flutter pub get` inside this directory.
- VLM auth/network errors: run `测试配置` in Settings and check the classified message.
