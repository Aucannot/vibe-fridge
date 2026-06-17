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

The strongest remaining product gap is platform-specific notification
validation. Flutter Web cold-start text now has a native HTML loading screen to
cover the short CanvasKit font fallback window, and the latest mobile Web smoke
check confirmed it hands off cleanly to the rendered Home screen.

## Verification

- `flutter test`: passed after the latest beta fixes including Android reminder
  restoration, Web route cleanup, notification channel coverage, startup error
  copy coverage, plus AI recipe and order-recognition error-copy coverage,
  48 tests.
- `flutter analyze`: passed after the latest beta fixes including Web route
  cleanup, direct Web detail URL hash cleanup, notification channel coverage,
  and the edit-page Material fix.
- `flutter test test/local_notification_service_test.dart`: passed after the
  Android reminder scheduler refactor, 6 tests.
- `flutter build web --debug --no-wasm-dry-run`: passed after the latest beta
  fixes including Web route cleanup, direct Web detail URL hash cleanup,
  startup error copy coverage, and the edit-page Material fix.
- Web build output now includes the native HTML loading screen used to cover
  Flutter Web's cold-start font fallback window.
- App self-check from Settings: passed, 15/15.
- Fresh Web smoke check on a new local port: no new console warnings or errors
  for the latest build.
- Mobile Web cold-start visual smoke check on port 54331: the native loading
  screen handed off to the rendered Home screen at 390 x 844 with no blank
  viewport and no browser warning or error logs.
- Mobile Web detail URL smoke check on port 54331: tapping the Home priority
  row for `面包` opened the inventory detail page and kept the address bar at
  `?route=items%2Fitem%2Fitem-bread-1` with no hash fragment and no browser
  warning or error logs.
- Mobile Web recipe consumption smoke check on port 54332: opened the Recipes
  tab, opened `快手蛋奶早餐`, used `做这道菜并扣减库存`, returned to
  `?route=recipes`, saw `库存已扣减`, and verified priority counts dropped
  from `鸡蛋 12个` / `鲜牛奶 2盒` to `鸡蛋 11个` / `鲜牛奶 1盒` with no
  browser warning or error logs.
- Mobile Web shopping-loop smoke check on port 54333: opened the shopping tab,
  added the `感冒药` replenishment suggestion to the list, checked it as
  purchased, confirmed `采购项入库`, saw `已入库 1 项`, and verified the
  catalog count for `感冒药` increased from 1 to 2 with no browser warning or
  error logs.
- Mobile Web Settings self-check smoke check on port 54334: opened Settings,
  ran `运行自验收`, saw the card switch to `全部通过` with `15/15`, verified
  the detailed check list rendered readable rows for inventory, reminders,
  recipes, shopping, batch edits, and history, with no browser warning or error
  logs.
- Mobile Web manual-add smoke check on port 54335: opened Add, entered
  `内测手动橙子` with the default quantity and purchase date, saved it, returned
  to the catalog, saw the new item with `1` batch, then opened its item-profile
  detail at `?route=items%2Fwiki%2F...` with no browser warning or error logs.
- Mobile Web inventory-detail quantity smoke check on port 54336: opened the
  Home priority row for `鲜牛奶`, reached `?route=items%2Fitem%2Fitem-milk-1`,
  increased quantity from `2 盒` to `3 盒`, verified the fact row updated, then
  decreased it back to `2 盒` with no browser warning or error logs.
- Mobile Web order-text import smoke check on port 54337: pasted
  `BETA-TEXT-001` with `苹果 4个` and `酸奶 2盒`, reviewed `2/2 已选` with
  correct quantities and units, confirmed batch import, saw `导入完成` with
  `新增 2`, and verified the catalog showed `苹果 4` and `酸奶 2` with no
  browser warning or error logs.
- Mobile Web consume/history smoke check on port 54338: opened `面包` inventory
  detail, confirmed `标记已消耗`, returned to Home with the pending reminder
  count reduced from 2 to 1, then opened `?route=items&view=history` and saw
  `面包` marked `已消耗`, with no browser warning or error logs.
- Mobile Web inventory-table export smoke check on port 54339: opened Settings,
  used `导出库存表格`, and saw `库存表格已导出` feedback with no browser
  warning or error logs. Codex In-app Browser does not support download events,
  so this proves the live UI trigger and success feedback but not downloaded
  file persistence.
- Mobile Web catalog search smoke check on port 54340: opened the Items tab,
  searched for `牛奶`, saw the catalog narrow to `鲜牛奶` while keeping the
  expiring mini-card visible, then opened the result to
  `?route=items%2Fwiki%2Fwiki-milk` with no browser warning or error logs.
- Mobile Web inventory-edit smoke check on ports 54341 and 54342: opening the
  `鲜牛奶` edit screen originally produced a Flutter debug assertion about
  `SwitchListTile` inside a decorated card; after wrapping the switch tile in
  its own transparent `Material`, the edit screen opened with no browser
  warning or error logs, and saving `存放位置` as `冷藏` was visible on the
  inventory detail facts after reload.
- Mobile Web item-profile edit smoke check on port 54349: editing `鲜牛奶`
  originally saved data but left the detail page stale and produced a Flutter
  debug assertion from an async-looking `setState` refresh callback; after
  reworking the detail refresh, saving a second description marker returned to
  the item-profile detail with the new description visible immediately and no
  new browser warning or error logs.
- Mobile Web item-profile batch-location smoke check on port 54350: opened
  `鲜牛奶`, entered batch mode, selected the inventory batch, used `改位置`,
  chose `冷冻`, saw `已修改 1 条库存的位置`, verified the batch card showed
  `位置 冷冻`, then opened the inventory detail and confirmed the fact row also
  showed `存放位置 冷冻` with no browser warning or error logs.
- Mobile Web item-profile batch-category smoke check on port 54351: opened
  `鲜牛奶`, entered batch mode, selected the inventory batch, used `改分类`,
  chose `日用品`, saw the item-profile category and inventory detail category
  both update to `日用品`, with no browser warning or error logs. The first
  pass exposed misleading success copy that described the change as one
  inventory batch's category even though category is stored on the item
  profile, so the sheet title and success feedback were clarified.
- Mobile Web item-profile batch-consume smoke check on port 54353: opened
  `鲜牛奶`, selected one active inventory batch from item-profile batch mode,
  confirmed `批量标记消耗`, and verified the original `2盒` batch became one
  `1盒` active batch plus one `1盒` consumed batch with no browser warning or
  error logs. The first pass exposed that the facts card said `库存批次 1`
  while the batch list showed both active and consumed rows, so the facts label
  was clarified to `使用中批次`.
- Mobile Web consume-restore smoke check on port 54355: opened `面包`
  inventory detail, confirmed `标记已消耗`, verified it appeared in History as
  `已消耗`, opened the consumed detail, used `恢复为使用中`, then verified
  History became empty and the catalog/expiring section showed `面包 1袋`
  again with no browser warning or error logs.
- Mobile Web single-inventory delete smoke check on port 54356: opened
  `感冒药` inventory detail, used the top-right delete action, confirmed the
  destructive dialog `删除库存记录`, returned to the catalog, verified
  `感冒药` changed to `0` batches, then reopened the deleted direct detail URL
  and saw the friendly `库存记录不存在` empty state with no browser warning or
  error logs.
- Mobile Web direct detail URL smoke check on port 54344: loaded
  `?route=items%2Fitem%2Fitem-milk-1` directly, waited for route cleanup, and
  verified the address bar stayed on the query route without a Flutter hash
  fragment while rendering the inventory detail page with no browser warning
  or error logs.
- Targeted UI-copy grep for engineering terms found no new actionable
  user-facing leaks. The remaining AI `JSON` wording is confined to prompts or
  internal exceptions and is wrapped by the user-friendly recipe fallback copy.
- `flutter build macos --debug`: blocked by local environment. Flutter reached
  Xcode dependency resolution, then failed because the active developer
  directory is Command Line Tools and `xcodebuild` is unavailable to `xcrun`.
- `flutter build apk --debug`: blocked by local environment after downloading
  Flutter Android artifacts; Flutter reported no Android SDK.
- `xmllint --noout mobile/android/app/src/main/AndroidManifest.xml`: passed
  after adding the Android boot/package-replaced reminder receiver.
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
- Web detail route cleanup fix compiles in the Web build so inventory and
  item-profile detail links are set up to keep the app's query-route format
  instead of retaining Flutter hash fragments.
- Web route cleanup now covers the remaining detail entry points from home
  priority rows, item-profile batch rows, and recipe cards.
- Web cold-start loading screen compiles into `build/web/index.html` and uses
  system Chinese fonts until Flutter's first frame has settled.
- Web app metadata now uses the product name, inventory-focused description,
  and warm theme colors instead of Flutter template defaults.
- macOS camera and photo permission prompts now use Chinese product language
  and describe the user-triggered photo workflows.
- Android's system notification channel now uses the broader product term
  `库存提醒` instead of only expiry-focused wording.
- Android's system notification channel now also includes a system-settings
  description, `库存到期和处理提醒`, so users can recognize what the reminder
  covers before enabling or muting it.

## Passing Checks Observed

- Home dashboard renders summary, expiring priority inventory, and category
  distribution clearly after fonts load.
- Home total action badge opens the cleanup-focused inventory list.
- Home expiring-priority rows open inventory batch detail.
- Catalog expiring mini cards open inventory batch detail.
- Catalog search filters the live mobile Web list and search results still open
  the matching item-profile detail route.
- Manual add flow saved a test item, returned to the catalog, and the new
  item-profile detail opened from the live mobile Web UI.
- Inventory detail quantity controls update visibly in both directions and the
  detail fact row stays in sync.
- Inventory edit now opens without Flutter debug assertions in the live mobile
  Web UI, and edited storage location data persists into the detail facts.
- Item-profile edit now saves from the live mobile Web UI and refreshes the
  detail header to the edited description without a manual browser reload.
- Item-profile batch mode can update selected inventory storage locations, and
  both the batch card and inventory detail fact row stay in sync.
- Item-profile batch category changes update the profile-level category and
  the inventory detail fact row consistently.
- Item-profile batch consume can split a multi-quantity batch into active and
  consumed rows while keeping the active-batch count understandable.
- Direct Web detail URLs now clean up late Flutter hash fragments and keep the
  copyable address bar on the app's query-route format.
- Marking an inventory batch consumed removes it from active priority handling
  and shows it in the history tab as `已消耗`.
- Restoring a consumed inventory batch from its detail page moves it out of
  History and back into active catalog and expiring views.
- Deleting a single inventory batch returns to the catalog, updates the item
  count, and leaves a friendly empty state for stale direct detail URLs.
- Shopping list checkbox moves a pending item into the purchased section.
- Purchased shopping items can be converted into inventory after confirmation,
  and the catalog count updates in the live mobile Web UI.
- Recipes page lists priority consumables and concrete recipe suggestions.
- Recipe detail shows consumed inventory, missing ingredients, steps, and the
  inventory deduction action.
- Running a recipe deduction updates priority consumable counts in the live
  mobile Web UI and returns to the recipe list with user feedback.
- Settings self-check completed and cleaned up its temporary data, and the
  mobile Web UI shows the 15/15 result plus readable per-check timings.
- Settings inventory-table export can be triggered from the live mobile Web UI,
  and the app shows success feedback without console warnings or errors.
- Repository backup/restore tests cover pre-restore snapshots, replacement
  restore, post-restore health checks, and backup reminder clearing.
- Repository backup/restore tests now also reject incomplete or damaged backup
  files before any current data is replaced or a restore snapshot is created.
- Repository export tests now verify the user-facing inventory table uses
  readable column names, omits internal identifiers, and formats dates as
  plain calendar dates.
- Repository export tests now verify the inventory table starts with a UTF-8
  marker so spreadsheet apps can detect Chinese text more reliably.
- Notification payload tests cover pending reminders, ignored reminders, title
  and body content, schedule time, and serialized timestamp fields.
- Local notification sync result tests now cover supported, unauthorized,
  unsupported, missing implementation, and unknown failure copy.
- Local notification permission channel tests now cover native status parsing
  and platform-exception fallback copy.
- Local notification permission copy tests now cover the unsupported-platform
  hint shown in Settings when native scheduling actions are disabled.
- Local notification channel tests now cover tap callbacks, malformed tap
  payloads, and safe launch-target fallback when the platform call fails.
- Android notification scheduling now persists pending reminder payloads and
  registers boot/package-replaced restoration points; runtime proof still needs
  an Android SDK/device environment.
- Bootstrap error page tests now verify startup diagnostics remain copyable
  without exposing technical details on screen by default.
- AI recipe fallback tests now verify service failures still return rule-based
  suggestions without exposing HTTP status codes or server text to users.
- Order-recognition error-copy tests now verify HTTP status codes and service
  response snippets stay out of user-facing configuration messages.
- Pasted order-text import now has live mobile Web coverage from text parsing
  through review confirmation and catalog verification.

## Fixes Made During This Pass

- Reworded user-visible settings copy to avoid exposing implementation terms:
  `订单识别 VLM` became `订单识别 AI`, and the API key helper now says it is
  stored in the local secure area.
- Reworded order-recognition configuration fields and error hints from
  endpoint/model/key terminology to service address, model name, and API
  secret language, including response-format failure details.
- Centralized order-recognition failure messages so configuration tests show
  user-actionable guidance instead of raw HTTP status or response text.
- Reworded the add-item order-recognition setup prompt to use API secret
  language consistently with Settings.
- Reworded the self-check notification item to avoid exposing `payload`.
- Reworded the add-item order-recognition prerequisite snackbar to ask for the
  order-recognition service configuration instead of VLM endpoint/model details.
- Hid startup diagnostic details behind the copy action so a failed launch does
  not show file paths, storage errors, or stack traces directly to users.
- Reworded AI recipe fallback failures so users see that rule suggestions are
  available instead of raw HTTP or service response details.
- Moved the order-recognition configuration check before local image copying,
  so an unconfigured order-recognition attempt does not leave an unused order
  screenshot in app storage.
- Expanded pasted order text unit parsing so common units like `枚` and `根`
  do not get stuck in the item name or default to quantity 1.
- Disabled local notification action buttons on unsupported platforms so users
  do not have to click a dead-end action to learn that reminders cannot be
  scheduled there.
- Added a short Settings hint for unsupported local notification platforms so
  users know reminder items still appear in the home-page action list.
- Added backup structure validation before restore so malformed backup files
  fail early without changing current inventory data.
- Simplified the backup restore success message so it does not expose an
  implementation-level restored row count as if it were a user-facing item
  count.
- Reworded local notification sync failures so platform/plugin error codes are
  not shown directly to users.
- Added Android reminder restoration after device reboot or app update by
  persisting scheduled reminder payloads and replaying them from a receiver.
- Added Flutter-side notification permission channel contract tests for native
  status parsing and platform-exception fallback.
- Added Flutter-side notification channel contract tests for notification tap
  delivery and launch-target failure fallback.
- Reworked the exported inventory table columns to remove internal identifiers
  and use user-readable Chinese headers.
- Reworked inventory table dates to use `yyyy-MM-dd` instead of timestamp-like
  values.
- Added a UTF-8 marker to the exported inventory table to reduce Chinese text
  mojibake in desktop spreadsheet apps.
- Fixed nullable SQL query arguments in shopping-list de-duplication and legacy
  duplicate detection so sqflite no longer logs a future-breaking null argument
  warning.
- Cleaned up Web detail route syncing so copied detail URLs are no longer set
  up to keep both the app route query and a Flutter hash route after
  navigation; this pass verified compilation, while browser address-bar
  automation was unavailable locally.
- Extended the same route cleanup pattern to home priority rows, item-profile
  batch rows, and recipe detail navigation so those natural beta-user paths
  avoid mixed query/hash URLs too.
- Strengthened Web route hash cleanup with delayed retries so direct detail
  URLs also remove late Flutter hash fragments after the Navigator settles.
- Added a lightweight Web loading screen that uses native system Chinese fonts,
  matches the app's warm visual style, honors reduced-motion preferences, and
  hides shortly after Flutter's first frame to reduce the cold-start square-text
  flash.
- Replaced Web/PWA template metadata so browser tabs and installed app surfaces
  show `vibe-fridge`, the app's actual inventory purpose, and product colors.
- Reworded macOS camera and photo permission prompts to match the app's Chinese
  UI and the actual user actions that request access.
- Reworded the Android notification channel display name from expiry-only
  language to inventory-reminder language.
- Wrapped the inventory edit reminder switch in its own transparent `Material`
  so Flutter no longer reports hidden ListTile ink/background behavior when a
  beta user opens the edit screen.
- Reworked item-profile detail refresh after editing so saved profile changes
  reload from controller changes and remain visible without a manual browser
  refresh.
- Clarified item-profile batch category copy so the picker and success
  feedback describe the profile-level category being changed instead of
  implying only one inventory batch owns the category.
- Clarified the item-profile facts card count from `库存批次` to `使用中批次`
  because the batch list also includes consumed rows after partial
  consumption.
- Reworked remaining inventory-detail reload callbacks so edit and image
  updates refresh without returning a `Future` from `setState`.

## Remaining Risks

- Android and macOS local notification behavior still needs device or desktop
  runtime validation on a machine with Android SDK and full Xcode/CocoaPods.
- The native notification implementations still need runtime proof even though
  the Dart service degrades cleanly when permission is missing, unsupported, or
  the platform channel is absent.
