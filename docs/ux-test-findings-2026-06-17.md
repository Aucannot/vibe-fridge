# UX Test Findings - 2026-06-17

Scope: exploratory beta-user testing against the Flutter Web debug build served
locally from `mobile/build/web`.

Viewport: mobile-sized browser viewport, 390 x 844.

Focus: whether a user can complete the main app jobs: understand the dashboard,
add inventory, inspect inventory detail, use the shopping loop, consume via
recipes, and run the built-in acceptance check.

## Summary

The app is now usable for the core home-inventory loop. A beta user can add an
item, see it in the catalog, open expiring inventory detail, adjust quantity,
add an item to the shopping list, mark it purchased, convert it back to
inventory, open recipe suggestions, and deduct inventory after cooking.

The strongest remaining product gaps are platform-specific validation and a
short Flutter Web font-loading flash where Chinese text can briefly render as
square placeholders on a cold port before the font becomes available.

## Verification

- `flutter analyze`: passed.
- `flutter test`: passed.
- `flutter build web --debug --no-wasm-dry-run`: passed.
- App self-check from Settings: passed, 15/15.
- Fresh Web smoke check on a new local port: no new console warnings or errors
  for the latest build.
- `flutter build macos --debug`: blocked by local environment. Flutter reached
  Xcode dependency resolution, then failed because the active developer
  directory is Command Line Tools and `xcodebuild` is unavailable to `xcrun`.
- `flutter build apk --debug`: blocked by local environment after downloading
  Flutter Android artifacts; Flutter reported no Android SDK.
- `flutter doctor -v`: confirmed no Android SDK, incomplete Xcode, missing
  CocoaPods, no Chrome binary, and sandboxed network checks failing without
  elevated network access.
- `python3 tools/perf_inventory_sqlite.py`: passed. Core inventory queries
  remained well under thresholds with 5,000 generated records: exact catalog
  search 0.683 ms, category filter 2.177 ms, today-action query 1.839 ms,
  active totals 0.764 ms, wiki count 0.012 ms, category counts 2.253 ms.
- Mobile Web smoke check on port 54326: pasted order text with `鸡蛋 12枚`
  and `香蕉 3根` now parses into importable items with the correct quantities
  and units, with no browser warning or error logs.
- Mobile Web settings check on port 54328: unsupported local notification
  actions now render disabled while keeping the platform-unavailable status
  visible, with no browser warning or error logs.

## Passing Checks Observed

- Home dashboard renders summary, expiring priority inventory, and category
  distribution clearly after fonts load.
- Home total action badge opens the cleanup-focused inventory list.
- Home expiring-priority rows open inventory batch detail.
- Catalog expiring mini cards open inventory batch detail.
- Manual add flow saved a test item and returned to the catalog with feedback.
- Inventory detail quantity controls update visibly.
- Shopping list checkbox moves a pending item into the purchased section.
- Purchased shopping items can be converted into inventory after confirmation.
- Recipes page lists priority consumables and concrete recipe suggestions.
- Recipe detail shows consumed inventory, missing ingredients, steps, and the
  inventory deduction action.
- Running a recipe deduction updates priority consumable counts.
- Settings self-check completed and cleaned up its temporary data.
- Repository backup/restore tests cover pre-restore snapshots, replacement
  restore, post-restore health checks, and backup reminder clearing.
- Notification payload tests cover pending reminders, ignored reminders, title
  and body content, schedule time, and serialized timestamp fields.

## Fixes Made During This Pass

- Reworded user-visible settings copy to avoid exposing implementation terms:
  `订单识别 VLM` became `订单识别 AI`, and the API key helper now says it is
  stored in the local secure area.
- Reworded the self-check notification item to avoid exposing `payload`.
- Reworded the add-item order-recognition prerequisite snackbar to ask for the
  order-recognition service configuration instead of VLM endpoint/model details.
- Moved the order-recognition configuration check before local image copying,
  so an unconfigured order-recognition attempt does not leave an unused order
  screenshot in app storage.
- Expanded pasted order text unit parsing so common units like `枚` and `根`
  do not get stuck in the item name or default to quantity 1.
- Disabled local notification action buttons on unsupported platforms so users
  do not have to click a dead-end action to learn that reminders cannot be
  scheduled there.
- Fixed nullable SQL query arguments in shopping-list de-duplication and legacy
  duplicate detection so sqflite no longer logs a future-breaking null argument
  warning.

## Remaining Risks

- Android and macOS local notification behavior still needs device or desktop
  runtime validation on a machine with Android SDK and full Xcode/CocoaPods.
- Flutter Web can show square placeholders for Chinese text briefly during cold
  font loading; it recovered after waiting a few seconds in this pass.
- Web detail URLs can include Flutter's hash route alongside the query route,
  which is not blocking but makes copied URLs less tidy.
- The native notification implementations still need runtime proof even though
  the Dart service degrades cleanly when permission is missing, unsupported, or
  the platform channel is absent.
