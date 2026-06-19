# UX Test Findings - 2026-06-17

Scope: exploratory beta-user testing against the Flutter Web debug build served
locally from `mobile/build/web`.

Viewport: mobile-sized browser viewport, 390 x 844.

Focus: whether a user can complete the main app jobs: understand the dashboard,
add inventory, inspect inventory detail, use the shopping loop, consume via
recipes, and run the built-in app self-check.

## Summary

The app is now usable for the core home-inventory loop. A beta user can add an
item, see it in the catalog, open expiring inventory detail, adjust quantity,
add an item to the shopping list, mark it purchased, convert it back to
inventory, open recipe suggestions, and deduct inventory after cooking.

The strongest remaining product gap is platform-specific notification runtime
validation. Settings now has an immediate test-notification action to make
permission and delivery checks faster on Android/macOS, but scheduled reminder
delivery and notification-click routing still require target-platform manual
validation. Flutter Web cold-start text now has a native HTML loading screen to
cover the short CanvasKit font fallback window, and the latest mobile Web smoke
check confirmed it hands off cleanly to the rendered Home screen.

## Beta Readiness

Verdict: ready for continued Web beta testing of the core inventory workflow,
but not yet ready to claim Android/macOS notification readiness.

Proven enough for beta:

- Home dashboard, today actions, reminder snooze/ignore, item catalog, item
  profile, inventory detail, manual add, order-text import, shopping list,
  recipes, backup/export, restore/import copy, settings, and app self-check all
  have passing automated or browser-smoke evidence.
- Web deep links and browser Back/Forward now preserve hash-free query routes
  across catalog search detail, inventory detail, and recipe detail paths.
- User-facing copy has been scrubbed across the main tested flows to avoid raw
  database, migration, legacy implementation, and diagnostic details.

Not proven yet:

- Android/macOS scheduled local notification runtime behavior. Dart fallback
  behavior, the Settings test-notification action, Android manifest wiring
  tests, macOS bridge wiring source tests, repository notification payload
  tests, and macOS native scheduling-payload construction, permission-status
  mapping, and tap payload handoff tests are covered, but real device/desktop
  scheduled reminder delivery and user-click behavior still need runtime
  validation on the target platforms.
- Web update experience on an existing origin. The custom bootstrap no longer
  registers Flutter's service worker, clears stale registrations, and deletes
  stale Flutter Cache Storage entries when the current index loads, but an old
  service worker or browser cache can still mask the first request for the new
  index during manual validation.

Recommended next beta gate:

- Run one Android debug build on a machine with Android SDK configured, then
  manually verify Android notification permission, scheduled reminder delivery,
  and notification click opening the matching inventory detail. On macOS, build
  plus native scheduling payload, permission-status mapping, and tap payload
  handoff are now covered locally; the next gate is manual permission,
  delivery, and system notification click validation.

Platform notification checklist for that gate:

- Build and launch Android debug on a device or emulator with notification
  permission support; verify Settings shows a supported permission state.
- On Android, request notification permission from Settings, send a test
  notification, sync reminders, wait for a due reminder, tap the delivered
  reminder notification, and confirm the matching inventory detail opens.
- Restart the Android app or emulator after reminders are scheduled, then
  confirm boot/package-replaced restoration still delivers the stored reminder.
- Build and launch macOS debug with full Xcode/CocoaPods tooling; verify
  Settings shows a supported permission state.
- On macOS, request notification permission, send a test notification, sync
  reminders, wait for a due reminder, tap the delivered reminder notification,
  and confirm the matching inventory detail opens.
- Re-run the Settings app self-check after platform notification testing to
  confirm notification experiments did not leave invalid inventory, shopping,
  recipe, reminder, or history state behind.

## Verification

- `flutter test`: passed after the latest beta fixes including Android reminder
  restoration, Web route cleanup, the `MaterialApp.router` browser-history fix,
  notification channel coverage, startup error copy coverage, AI recipe and
  order-recognition error-copy coverage, plus the generic error snackbar
  detail-copy coverage, notification tap controller handoff coverage, and
  notification permission-to-sync controller coverage, 57 tests; passed again
  after the macOS native notification request builder extraction. Passed again
  after adding the custom Web bootstrap guard, 58 tests. Passed again after
  adding Android notification wiring source tests, 60 tests. Passed again after
  adding macOS notification wiring source tests, 62 tests. Passed again after
  extending app self-check backup coverage, 64 tests. Passed again after adding
  the Settings test-notification action and channel coverage, 67 tests. Passed
  again after adding Settings widget coverage for the test-notification action,
  68 tests.
- `flutter test test/app_error_snackbar_test.dart`: passed after clarifying
  the generic error snackbar copy action and covering that technical details
  stay hidden from the visible message.
- `flutter test test/inventory_repository_test.dart`: passed after the
  no-date order duplicate fix and backup-reminder copy cleanup, 19 tests.
  Passed again after adding inventory-table export coverage for commas,
  quotes, and newline characters in user-entered fields, 20 tests. Passed
  again after adding backup round-trip coverage for inventory tags, reminder
  logs, and shopping-list data, 21 tests. Passed again after extending the
  Settings app self-check to verify backup content includes inventory, tags,
  reminder logs, and shopping-list data, 21 tests.
- `flutter analyze`: passed after the latest beta fixes including Web route
  cleanup, direct Web detail URL hash cleanup, the `MaterialApp.router`
  browser-history fix, notification channel coverage, the edit-page Material
  fix, and no-date order duplicate handling; passed again during final route
  code review, after the final Settings copy cleanup, and after adding the
  notification tap and permission-to-sync controller tests, and after the macOS
  native notification request builder extraction, with no issues.
- `flutter test test/local_notification_service_test.dart`: passed after the
  Android reminder scheduler refactor, notification tap controller handoff
  coverage, notification permission-to-sync controller coverage, and Settings
  test-notification flow coverage, 12 tests.
- `flutter test test/settings_screen_test.dart`: passed after adding widget
  coverage that renders the Settings test-notification action and verifies the
  button calls the notification service path.
- `flutter test test/android_notification_wiring_test.dart`: passed after
  adding Android source-level checks for notification manifest permissions,
  receivers, method-channel names, payload keys, scheduling persistence,
  boot/package-update restoration, and click handoff wiring.
- `flutter test test/macos_notification_wiring_test.dart`: passed after adding
  macOS source-level checks for method-channel names, native bridge methods,
  notification payload parsing, delegate presentation behavior, and system tap
  handoff into the launch target.
- `flutter test test/web_bootstrap_test.dart`: passed after adding the custom
  Web bootstrap guard that clears stale service workers without registering a
  replacement Flutter service worker; passed again after extending the guard to
  delete stale Flutter Cache Storage entries.
- `flutter build web --debug --no-wasm-dry-run`: passed after the latest beta
  fixes including Web route cleanup, direct Web detail URL hash cleanup,
  startup error copy coverage, the edit-page Material fix, and no-date order
  duplicate handling; passed again after extending the native Web loading
  screen delay to cover desktop CanvasKit font settling, again before the
  latest Settings smoke check, and again as a final current-worktree Web build
  gate after the browser-history route fix. Passed again after pushing the
  beta notification and routing validation commit, then served on port 54390
  for post-push smoke testing. Passed again after adding the custom Web
  bootstrap; generated `flutter_bootstrap.js` now calls `_flutter.loader.load()`
  without `serviceWorkerSettings` and contains the stale-registration cleanup.
- `flutter build macos --debug`: passed after the user completed the local
  Xcode installation and license flow. The build produced
  `build/macos/Build/Products/Debug/vibe-fridge.app`; Flutter also generated
  Swift Package Manager integration for the macOS project and warned that
  `flutter_secure_storage_macos` still uses CocoaPods. Passed again after
  extracting and testing the macOS notification request builder and permission
  status mapper, and again after adding the native tap payload handoff helper.
- `xcodebuild test -workspace Runner.xcworkspace -scheme Runner -configuration
  Debug -destination 'platform=macOS' -derivedDataPath
  /private/tmp/vibe-fridge-xcode-derived-tap -clonedSourcePackagesDirPath
  /private/tmp/vibe-fridge-xcode-spm-tap`:
  passed after fixing the RunnerTests `TEST_HOST` product path and importing
  the app module as `vibe_fridge`. RunnerTests now covers macOS notification
  request construction, malformed payload skipping, the 60-second minimum
  notification trigger delay, native permission-status channel mapping, and
  native tap payload handoff into the launch target plus Flutter event path.
- `flutter run -d macos`: launched the debug macOS target successfully and
  exposed a Dart VM Service. The app process started, though `open` could not
  automatically foreground the window in this shell session.
- `flutter build apk --debug`: attempted after the latest route and platform
  checks. Dependency resolution completed, but the local environment could not
  continue because no Android SDK was found; this did not produce an app compile
  error, but leaves Android native runtime validation unproven in this
  environment.
- Native notification bridge static review: Android and macOS implementations
  use the same `vibe_fridge/local_notifications` method channel as Dart,
  preserve `itemId` in scheduled notification payloads, expose launch/tap
  callbacks back to Flutter, and include boot or app-start recovery paths where
  the platform supports them. Android manifest/channel/payload-key wiring and
  macOS bridge/delegate wiring are now covered by
  `android_notification_wiring_test.dart` and
  `macos_notification_wiring_test.dart`. No obvious channel-name, payload-key,
  or click callback mismatch was found, but this does not replace runtime
  validation on real Android/macOS environments.
- Final targeted user-facing copy grep: scanned Flutter screens, widgets, and
  bootstrap UI for database, SQLite, migration, legacy, Wiki, JSON/id, and
  related implementation wording. Remaining matches were internal identifiers,
  file extensions, prompts, hidden diagnostics, or already-user-facing product
  language. The only visible wording tightened in this pass was the order
  recognition key copy, rephrased from storage terminology to
  `密钥状态` / `本机安全保存` / `本机安全区域`.
- Web build output now includes the native HTML loading screen used to cover
  Flutter Web's cold-start font fallback window.
- Web bootstrap output now omits Flutter service-worker registration settings,
  unregisters stale same-origin service workers, and deletes stale Flutter
  Cache Storage entries before loading the app. A same-origin Settings smoke
  check on port 54390 loaded successfully with no active controller, no
  registrations, hidden loading screen, and no browser warnings or errors in
  this environment. After adding Cache Storage cleanup, the rebuilt Web output
  contained the cache-deletion calls, and a follow-up Settings smoke check on
  port 54390 loaded `vibe-fridge`, hid the loading screen, captured a non-empty
  page screenshot, and reported no browser warnings or errors.
- App self-check from Settings: passed, 15/15; passed again on the restarted
  latest Web target on port 54390 in about 354ms. After adding the backup
  content check and rebuilding Web, the current Settings self-check passed
  16/16 on port 54390 in about 372ms with no browser warning or error logs.
- Fresh Web smoke check on a new local port: no new console warnings or errors
  for the latest build.
- Mobile Web cold-start visual smoke check on port 54331: the native loading
  screen handed off to the rendered Home screen at 390 x 844 with no blank
  viewport and no browser warning or error logs.
- Desktop Web main-surface smoke check on port 54409 at 1280 x 720: opened
  Home, Items, Add, Recipes, and Settings. Home, Items, Add, and Settings used
  the centered content width and wider card layouts without overlap or console
  warnings/errors. The first desktop Recipes direct-load pass exposed that
  Flutter content with square Chinese glyphs could become visible before fonts
  settled; after extending the native loading screen's first-frame delay, port
  54411 kept the native loading screen visible during that window and then
  handed off to correctly rendered Chinese text with no browser warning or
  error logs.
- Mobile Web detail URL smoke check on port 54331: tapping the Home priority
  row for `面包` opened the inventory detail page and kept the address bar at
  `?route=items%2Fitem%2Fitem-bread-1` with no hash fragment and no browser
  warning or error logs.
- Mobile Web today-action reminder smoke check on port 54403: opened Home,
  tapped the `提醒到期 2` summary to verify it linked to the focused
  reminder-due inventory list at `?route=items&focus=reminderDue`, then returned
  to Home and used `稍后` on `面包` plus `忽略` on `鲜牛奶`. The Home list updated
  from `2项` to `1项` to `0项`, showed `今天没有待处理`, the top summary updated
  to `0件` and `提醒到期 0`, and the snackbars said
  `今天稍后再提醒：面包` and `今天不再提醒：鲜牛奶`, with no browser warning or
  error logs.
- Mobile Web recipe consumption smoke check on port 54332: opened the Recipes
  tab, opened `快手蛋奶早餐`, used `做这道菜并扣减库存`, returned to
  `?route=recipes`, saw `库存已扣减`, and verified priority counts dropped
  from `鸡蛋 12个` / `鲜牛奶 2盒` to `鸡蛋 11个` / `鲜牛奶 1盒` with no
  browser warning or error logs.
- Mobile Web direct recipe URL smoke check on port 54386: loaded
  `?route=recipes%2Fquick-breakfast` directly and verified it opened the
  `快手蛋奶早餐` detail page with inventory use, missing ingredients, and steps;
  tapping back returned to `?route=recipes`, and both URLs stayed hash-free
  with no browser warning or error logs.
- Desktop Web recipe browser-history smoke check on fresh port 54390 after the
  `MaterialApp.router` fix: opened `?route=recipes`, tapped
  `快手蛋奶早餐` to reach `?route=recipes%2Fquick-breakfast`, used browser Back
  to return to the recipe list, then browser Forward to reopen the same recipe
  detail. Both transitions preserved hash-free query routes and produced no
  browser warning or error logs.
- Post-push desktop Web target smoke check on restarted port 54390: opened
  Settings, switched to Recipes, verified the URL became `?route=recipes`,
  opened `快手蛋奶早餐` at `?route=recipes%2Fquick-breakfast`, and used browser
  Back to return to `?route=recipes` with the recipe list restored.
- Desktop Web direct recipe URL regression check on port 54381 after switching
  the root app shell to `MaterialApp.router`: loaded
  `?route=recipes%2Fquick-breakfast` directly and verified it opened
  `快手蛋奶早餐` with inventory use, missing ingredients, and steps. The URL
  stayed hash-free and no browser warning or error logs appeared.
- Mobile Web unknown recipe URL smoke check on port 54387: loaded an
  unrecoverable generated-style route,
  `?route=recipes%2Fai-recipe-old-generated-0`, and verified the app replaced
  it with `?route=recipes` while rendering the recipe list, with no hash
  fragment and no browser warning or error logs.
- Mobile Web AI-recipe fallback smoke check on port 54364: opened Recipes with
  no AI service configured, tapped `生成食谱`, saw the AI card switch to
  `规则兜底` with `AI 食谱未配置，已使用规则建议`, verified rule suggestions stayed
  visible, then used the reset button to return to the initial `生成食谱` state
  with no browser warning or error logs.
- Mobile Web recipe favorite/recent smoke check on port 54388: favorited
  `快手蛋奶早餐` from the Recipes list without navigating away, verified
  `收藏` appeared with `1 个常用方案`, opened the favorited recipe detail with
  the heart state preserved, unfavorited it from detail, returned to the list,
  and verified `收藏` disappeared while `最近生成` listed the viewed recipes,
  with no browser warning or error logs.
- Mobile Web AI-recipe success smoke check on ports 54383 and 54385: configured
  a localhost-only fake OpenAI-compatible endpoint, generated one AI recipe
  named `内测牛奶快手杯`, opened its detail, and verified inventory use,
  missing ingredients, steps, and no browser warning or error logs. The first
  pass exposed that a Chinese AI recipe id left the address bar as a mixed
  query/hash route; after canonicalizing Web route cleanup, the rebuilt detail
  URL stayed at `?route=recipes%2Fai-recipe-...` with no hash fragment.
- Mobile Web shopping-loop smoke check on port 54333: opened the shopping tab,
  added the `感冒药` replenishment suggestion to the list, checked it as
  purchased, confirmed `采购项入库`, saw `已入库 1 项`, and verified the
  catalog count for `感冒药` increased from 1 to 2 with no browser warning or
  error logs.
- Mobile Web manual shopping edit/convert smoke check on port 54395: added
  `shopping-edit-test` from the shopping tab with quantity `3`, unit `包`, and
  a note, edited it to quantity `5` with a new note, checked it as purchased,
  and converted it into inventory. The first pass exposed that the shopping
  note was lost after conversion; after preserving it as the inventory batch
  description without updating the item-profile description, the rebuilt Web
  app converted `shopping-note-test` and showed `描述 采购备注应保留` on the
  inventory detail facts card, while the item-profile header stayed
  `暂无描述`, with no browser warning or error logs. The temporary test
  inventory and profiles were cleaned up through the UI.
- Mobile Web uncategorized shopping conversion smoke check on port 54396:
  added `category-copy-test` from the shopping tab without selecting a
  category, converted it into inventory, and verified the shopping list,
  catalog card, item-profile facts card, and inventory-detail facts card all
  consistently used `未分类` instead of switching the converted inventory to
  `其他`, with no browser warning or error logs. The temporary test inventory
  and profile were cleaned up through the UI.
- Mobile Web catalog-to-shopping smoke check on port 54391: opened the item
  catalog, tapped the cart action on the `感冒药` row, saw
  `已加入采购清单：感冒药` without leaving the catalog, opened the Shopping view,
  verified `待采购 1` contained `感冒药` with quantity `1` and source-note copy,
  then deleted the pending item and verified `待采购 0` while `感冒药` returned
  to replenishment suggestions, with no browser warning or error logs.
- Mobile Web focused-inventory shopping smoke check on port 54392: opened Home,
  tapped the `提醒到期 2` tile to reach `?route=items&focus=reminderDue`,
  added `面包` to the shopping list from the focused inventory card without
  leaving that list, opened the Shopping view, verified `待采购 1` contained
  `面包` with quantity `1袋` and source-note copy, then deleted it and verified
  `待采购 0` while `面包` returned to replenishment suggestions, with no browser
  warning or error logs.
- Mobile Web Settings self-check smoke check on port 54334: opened Settings,
  ran the app self-check, saw the card switch to `全部通过` with `15/15`, verified
  the detailed check list rendered readable rows for inventory, reminders,
  recipes, shopping, batch edits, and history, with no browser warning or error
  logs.
- Desktop Web Settings self-check smoke check on fresh port 54372 after a
  rebuild: opened Settings, verified the current `应用自检` / `运行自检` copy,
  ran the app self-check, saw `全部通过` with `15/15` in about 397ms, and saw no
  browser warning or error logs for the fresh origin. A same-port reload on
  port 54371 still showed older self-check copy after rebuilding, indicating
  older same-origin cache or previous registration state can keep stale Web
  assets during validation. The Web bootstrap now avoids registering a
  replacement Flutter service worker and clears stale registrations once the
  current index is loaded.
- Desktop and mobile Web Settings regression smoke check on fresh port 54384:
  opened Settings on the current build, verified backup/notification copy,
  scrolled to recipe preferences and app self-check, ran self-check, and saw
  `全部通过` with `15/15`. Then switched to 390 x 844, reloaded Settings,
  verified the mobile layout stayed readable, opened Recipes from the bottom
  navigation, and opened `快手蛋奶早餐` at
  `?route=recipes%2Fquick-breakfast` with no browser warning or error logs.
- Mobile Web recipe-preference settings smoke check on port 54363: opened
  Settings, scrolled to `食谱偏好`, entered `清淡内测`, `不吃辣`, `电饭煲`,
  changed time to `25` minutes and servings to `3`, saved, saw `食谱偏好已保存`,
  then reloaded Settings and verified all preference fields persisted with no
  browser warning or error logs.
- Mobile Web order-recognition settings smoke check on port 54366: opened
  Settings, scrolled to `订单识别 AI`, entered a fake local API key, saved,
  saw `订单识别配置已保存` and `已配置`, then reloaded Settings and verified the
  saved-key state persisted without showing the key in clear text. The pass
  then cleared the configuration through the confirmation dialog and verified
  `未配置` returned, with no browser warning or error logs. The `测试配置`
  action was intentionally not used, so the pass did not send an external
  request.
- Mobile Web order-recognition test-configuration smoke check on port 54382:
  ran Settings against a localhost-only fake OpenAI-compatible endpoint on
  port 54381, saved `订单识别 AI` configuration, verified the API key field
  cleared to the saved-key state without exposing the secret, tapped
  `测试配置`, saw `配置可用`, confirmed the fake service received one local POST,
  and then cleared the configuration back to `未配置` with no browser warning
  or error logs.
- Mobile Web demo-data reset smoke check on port 54367: added a user-created
  item named `reset-test-nori`, verified the Settings counts increased to
  `库存批次 5` and `物品资料 6`, then used `重置示例数据`. The confirmation copy
  clearly promised only built-in sample data would be rebuilt, the app showed
  `示例数据已重置，清理 9 条旧示例数据`, and the catalog still showed
  `reset-test-nori` afterward with no browser warning or error logs.
- Mobile Web manual-add smoke check on port 54335: opened Add, entered
  `内测手动橙子` with the default quantity and purchase date, saved it, returned
  to the catalog, saw the new item with `1` batch, then opened its item-profile
  detail at `?route=items%2Fwiki%2F...` with no browser warning or error logs.
- Mobile Web full-field manual-add smoke check on port 54368: opened Add,
  selected category `日用品`, selected storage location `冷藏`, entered
  `field-test-cleanser`, set unit `瓶`, chose expiry date `2026-06-25` from the
  date picker, and saved. The catalog immediately showed `日用品 · 冷藏 · 单位 瓶`
  with `7 天后到期`, the item-profile detail showed category, default unit,
  storage location, and the inventory batch dates, and the inventory detail
  showed expiry `2026-06-25`, reminder date `2026-06-22`, lead time `3 天`,
  and storage `冷藏`, with no browser warning or error logs.
- Mobile Web tagged manual-add smoke check on port 54369: opened Add, selected
  the tags `临期优先`, `常用`, and `易浪费`, entered `tag-test-cereal` with unit
  `袋`, and saved. The item-profile inventory row showed the first two tags
  (`临期优先 · 常用`) in its compact summary, and the inventory detail `标签`
  card showed all three saved tags with no browser warning or error logs.
- Mobile Web manual-add validation smoke check on port 54400: tried saving a
  blank manual item and verified the form stayed on the Add page with
  `请输入物品名称`; then entered `validation-test-item`, changed quantity to
  `0`, and verified the form showed `请输入大于 0 的整数` without saving. After
  correcting quantity to `2`, saving succeeded, the catalog showed the new
  item with quantity `2`, and the temporary inventory/profile were cleaned up
  through the UI with no browser warning or error logs.
- Mobile Web inventory-detail quantity smoke check on port 54336: opened the
  Home priority row for `鲜牛奶`, reached `?route=items%2Fitem%2Fitem-milk-1`,
  increased quantity from `2 盒` to `3 盒`, verified the fact row updated, then
  decreased it back to `2 盒` with no browser warning or error logs.
- Mobile Web order-text import smoke check on port 54337: pasted
  `BETA-TEXT-001` with `苹果 4个` and `酸奶 2盒`, reviewed `2/2 已选` with
  correct quantities and units, confirmed batch import, saw `导入完成` with
  `新增 2`, and verified the catalog showed `苹果 4` and `酸奶 2` with no
  browser warning or error logs.
- Mobile Web no-date duplicate order-text smoke check on port 54402: pasted
  `DUP-SMOKE-NODATE-001` without a purchase date and imported two rows. The
  first pass exposed that repeating the same order still showed `2 可入库` and
  would add duplicates because duplicate checks skipped rows without purchase
  dates. After allowing order-id/name duplicate checks without a purchase date,
  the rebuilt Web app showed `0 可入库`, `2 疑似重复`, `添加 0 个物品`, and the
  result dialog `没有新增物品` with `跳过 2`, with no browser warning or error
  logs.
- Mobile Web order-text review-edit smoke check on port 54393: pasted an order
  containing `内测复核苹果 4个`, a gift line, and `内测散装坚果` without a
  quantity. The review page showed `3/3 已选`, `1 可入库`, and `2 需要确认`;
  editing the apple quantity from `4` to `6` updated its summary pill, unselecting
  the gift left it out of the import, filling the nut unit as `袋` and tapping
  `标记已确认` changed the primary action to `添加 2 个物品`. Confirming import
  showed `新增 2`, `跳过 1`, `需要手动处理 0`, and the catalog showed only
  `内测复核苹果 6` and `内测散装坚果 1`, with no browser warning or error logs.
- Mobile Web bulk order-text backup reminder smoke check on ports 54397 and
  54398: pasted an order-like text containing a standalone reference
  `BETA-BACKUP-001` plus 10 inventory lines. The first pass imported the 10
  valid rows and verified Settings showed the backup reminder card with a
  cumulative unbacked-change note; it also exposed that the standalone
  reference appeared as a low-confidence item needing confirmation. After
  filtering standalone reference lines, the rebuilt Web app showed
  `10/10 已选`, `10 可入库`, no `需要确认`, and the first review card was
  `备份提醒米`, with no browser warning or error logs. The test used isolated
  local ports.
- Mobile Web backup reminder export-clear smoke check on port 54399: pasted 10
  valid order-text inventory rows, confirmed batch import with `新增 10` and
  `需要手动处理 0`, opened Settings, verified the `建议导出备份` card appeared
  with a cumulative unbacked-change note, tapped the card's `导出` action, saw
  `备份已导出`, and verified the reminder card disappeared with no browser
  warning or error logs. The test used an isolated local port.
- Mobile Web consume/history smoke check on port 54338: opened `面包` inventory
  detail, confirmed `标记已消耗`, returned to Home with the pending reminder
  count reduced from 2 to 1, then opened `?route=items&view=history` and saw
  `面包` marked `已消耗`, with no browser warning or error logs.
- Mobile Web history-search smoke check on port 54362: consumed `面包`, opened
  `?route=items&view=history`, searched `面包` and verified the consumed record
  remained visible, then searched `不存在测试词`. The first pass exposed that
  history search with no matches reused the true-empty copy `暂无历史记录`; after
  updating the filtered-empty state, the page showed `没有匹配记录` and clearing
  the search restored the `面包` row with no browser warning or error logs.
- Mobile Web inventory-table export smoke check on port 54339: opened Settings,
  used `导出库存表格`, and saw `库存表格已导出` feedback with no browser
  warning or error logs. Codex In-app Browser does not support download events,
  so this proves the live UI trigger and success feedback but not downloaded
  file persistence.
- Mobile Web backup export smoke check on port 54365: opened Settings, used
  `导出备份`, and saw `备份已导出` feedback with no browser warning or error
  logs. Codex In-app Browser does not support download events, so this proves
  the live UI trigger and success feedback but not downloaded file persistence.
- Mobile Web legacy-import preview smoke check on ports 54372 and 54373:
  opening Settings and tapping `导入旧版库存` originally produced a Flutter Web
  asset 404 warning while probing the optional ignored
  `legacy_inventory.local.json`; after checking the asset manifest before
  loading the override, the preview dialog opened on the empty bundled legacy
  file with all counts at 0 and no current-port browser warning or error logs.
- Mobile Web catalog search smoke check on port 54340: opened the Items tab,
  searched for `牛奶`, saw the catalog narrow to `鲜牛奶` while keeping the
  expiring mini-card visible, then opened the result to
  `?route=items%2Fwiki%2Fwiki-milk` with no browser warning or error logs.
- Mobile Web browser-history smoke check on port 54380 after switching the root
  app shell to `MaterialApp.router`, then repeated on port 54382 after making
  route parsing synchronous: loaded `?route=items&q=牛奶`, opened the `鲜牛奶`
  item-profile detail at `?route=items%2Fwiki%2Fwiki-milk`, used browser Back
  to return to the searched catalog with `q=牛奶`, then used browser Forward to
  reopen `?route=items%2Fwiki%2Fwiki-milk`. The URL stayed hash-free, the
  detail page rendered, and no browser warning or error logs appeared.
- Mobile Web catalog category-filter smoke check on port 54361: opened the
  Items tab, selected the `日用品` category chip, verified the URL changed to
  `?route=items&category=cat-daily` and the catalog list narrowed to `牙膏`,
  then tapped `全部` and verified the URL returned to `?route=items` with the
  mixed catalog list restored, with no browser warning or error logs.
- Mobile Web inventory-edit smoke check on ports 54341 and 54342: opening the
  `鲜牛奶` edit screen originally produced a Flutter debug assertion about
  `SwitchListTile` inside a decorated card; after wrapping the switch tile in
  its own transparent `Material`, the edit screen opened with no browser
  warning or error logs, and saving `存放位置` as `冷藏` was visible on the
  inventory detail facts after reload.
- Mobile Web inventory-edit tags/reminder smoke check on port 54370: opened
  `鲜牛奶` inventory detail, edited the batch, selected `临期优先` and `常用`,
  changed reminder lead time from `3` days to `1` day, and saved. The detail
  screen updated reminder date from `2026-06-18` to `2026-06-20`, showed
  `提前天数 1 天` in the facts card, and rendered the saved tags in the `标签`
  card with no browser warning or error logs.
- Mobile Web inventory-reminder disable smoke check on port 54371: opened
  `鲜牛奶` inventory detail, edited the batch, turned off `启用过期提醒`, and
  saved. The detail reminder card changed its status pill from `已启用` to
  `已关闭`, the facts card showed `提醒开关 关闭`, and the `提前天数` fact row
  was hidden while the expiry date stayed intact, with no browser warning or
  error logs.
- Mobile Web item-profile edit smoke check on port 54349: editing `鲜牛奶`
  originally saved data but left the detail page stale and produced a Flutter
  debug assertion from an async-looking `setState` refresh callback; after
  reworking the detail refresh, saving a second description marker returned to
  the item-profile detail with the new description visible immediately and no
  new browser warning or error logs.
- Mobile Web item-profile default-field edit smoke check on port 54394: added
  `profile-default-test`, opened its item-profile detail, edited default unit
  to `盒`, suggested shelf life to `14` days, default reminder lead time to
  `2` days, storage location to `冷藏`, and notes to `默认值内测备注`. The first
  pass exposed that notes saved but were invisible on the detail page; after
  showing non-empty notes in the profile facts card, the rebuilt Web app showed
  default unit, shelf life, reminder lead time, storage location, and notes
  immediately after save with no browser warning or error logs.
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
- Mobile Web item-profile batch-delete smoke check on port 54390: manually
  added `batch-delete-test` twice and verified the catalog merged them into
  one item profile with `2` batches, opened the item-profile detail, entered
  `批量` mode, used `全选`, confirmed `批量删除库存`, saw the detail page exit
  selection mode with `使用中批次 0`, `暂无库存`, and `已删除 2 条库存记录`,
  returned to the catalog and verified the profile count was `0` batches, then
  deleted the empty test profile, with no browser warning or error logs.
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
- Mobile Web item-profile delete smoke check on port 54389: added
  `profile-delete-test`, opened its item-profile detail, verified deleting the
  profile was blocked while `使用中批次` was `1`, deleted the inventory batch,
  saw the profile update to `使用中批次 0` with the `暂无库存` empty state,
  deleted the now-empty profile, verified catalog search showed
  `没有匹配物品`, and reopened the stale profile URL to the friendly
  `物品资料不存在` empty state with no browser warning or error logs.
- Mobile Web shopping-item delete smoke check on port 54357: opened the
  shopping tab, added the `面包` replenishment suggestion to the pending list,
  opened the row menu, confirmed the destructive `删除采购项` dialog, and
  verified the pending count returned to `0` while replenishment suggestions
  returned to `2`, with no browser warning or error logs.
- Mobile Web shopping-item edit smoke check on port 54358: opened the shopping
  tab, added the `面包` replenishment suggestion to the pending list, opened the
  row menu `编辑` sheet, changed quantity from `1` to `3`, replaced the note with
  `内测编辑备注`, saved, and verified the pending row immediately showed `3袋`
  plus the edited note with no browser warning or error logs.
- Mobile Web manual shopping-item smoke check on port 54359: opened the
  shopping tab, used the top `添加` action, entered `内测采购番茄`, changed
  quantity to `5`, set unit to `个`, added note `周末采购`, saved, and verified
  the pending list showed `内测采购番茄` with `5个` plus the note summary with no
  browser warning or error logs.
- Mobile Web shopping-item uncheck smoke check on port 54360: manually added
  `内测取消勾选鸡蛋`, marked it as purchased so it moved from `待采购 1` to
  `已买到 1` and showed the `入库` action, then unchecked it from the purchased
  section and verified it moved back to `待采购 1` while `已买到` returned to
  `0`, with no browser warning or error logs.
- Mobile Web direct detail URL smoke check on port 54344: loaded
  `?route=items%2Fitem%2Fitem-milk-1` directly, waited for route cleanup, and
  verified the address bar stayed on the query route without a Flutter hash
  fragment while rendering the inventory detail page with no browser warning
  or error logs.
- Desktop Web direct inventory-detail URL regression check on port 54381 after
  switching the root app shell to `MaterialApp.router`: loaded
  `?route=items%2Fitem%2Fitem-bread-1` directly and verified it rendered the
  `面包` inventory detail page. The URL stayed hash-free and no browser warning
  or error logs appeared.
- Initial targeted UI-copy grep for engineering terms found no new actionable
  user-facing leaks. The remaining AI `JSON` wording is confined to prompts or
  internal exceptions and is wrapped by the user-friendly recipe fallback copy.
- Follow-up UI-copy scan found inventory-detail import traces could display
  internal source values such as `legacy` and import batch identifiers for
  older imported rows. The detail page now maps that source to `旧版库存` and
  hides internal import batch ids from the user-facing trace.
- The same copy pass found Settings restore/import feedback using
  implementation-flavored terms like `恢复前快照`, `健康检查`, and `日志`.
  Those labels now use user-facing backup/check/detail wording instead.
- A follow-up Settings copy pass found the built-in check still used
  acceptance-style wording. The visible card, action, toast, and check-data
  labels now use `应用自检` language.
- Inspecting the app self-check failure path found failed check details would
  display raw Dart prefixes such as `Bad state:` before the useful message.
  Self-check failures now strip those technical prefixes before rendering.
- `flutter build macos --debug`: initially blocked by local environment.
  Flutter reached Xcode dependency resolution, then failed because the active
  developer directory was Command Line Tools and `xcodebuild` was unavailable
  to `xcrun`. After the user installed Xcode and accepted the license, the same
  command passed and produced the debug macOS app bundle.
- Xcode environment setup attempt after user approval: installed Homebrew
  `cocoapods`, `mas`, `xcodes`, and `aria2`. `xcodes install 26.5` could not
  proceed without Apple ID credentials, and `mas get 497799835` failed while
  looking up Xcode through the App Store API with a TLS error. The App Store
  Xcode page was opened for manual sign-in/install.
- `flutter run -d macos`: initially blocked by missing full Xcode, then passed
  after Xcode 26.5 was installed and selected. The app launched in debug mode
  and exposed a Dart VM Service; the shell reported `Failed to foreground app`
  after launch.
- `flutter build apk --debug`: blocked by local environment after downloading
  Flutter Android artifacts; Flutter reported no Android SDK.
- `xmllint --noout mobile/android/app/src/main/AndroidManifest.xml`: passed
  after adding the Android boot/package-replaced reminder receiver.
- `flutter doctor -v`: initially confirmed no Android SDK, incomplete Xcode,
  missing CocoaPods, no Chrome binary, and sandboxed network checks failing
  without elevated network access. After installing CocoaPods and rerunning with
  elevated network access, it confirmed CocoaPods 1.16.2 and healthy network
  resources. After Xcode 26.5 was installed and selected, doctor no longer
  reported missing first-launch components; only Android SDK, Chrome, and
  simulator runtime gaps remained relevant outside the macOS desktop target.
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
- Web route cleanup now also handles generated non-ASCII recipe identifiers,
  such as AI recipe titles in Chinese, without leaving Flutter hash fragments.
- Web route restoration now opens direct rule-recipe links such as
  `?route=recipes%2Fquick-breakfast` instead of only selecting the Recipes tab.
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
- Desktop Web renders the main Home, Items, Add, Recipes, and Settings surfaces
  in centered wide layouts without overlap, and the native loading screen now
  hides the desktop Chinese-font settling window before handing off to Flutter.
- Home total action badge opens the cleanup-focused inventory list.
- Home reminder-due summary opens the focused reminder inventory list, and
  today-action cards can be snoozed or ignored with immediate count/list
  refresh and user feedback.
- Home expiring-priority rows open inventory batch detail.
- Catalog expiring mini cards open inventory batch detail.
- Catalog search filters the live mobile Web list and search results still open
  the matching item-profile detail route.
- Catalog category chips filter the mobile Web list and can be cleared back to
  the full catalog without stale route state.
- Manual add flow saved a test item, returned to the catalog, and the new
  item-profile detail opened from the live mobile Web UI.
- Manual add also handles category, storage location, unit, and expiry-date
  fields end to end, with catalog, item-profile detail, and inventory detail
  staying consistent.
- Manual add saves processing-priority tags from the mobile Web UI, and tagged
  inventory displays those tags in item-profile and inventory detail views.
- Manual add validation blocks blank names and non-positive quantities with
  user-actionable inline messages, then allows saving once the user corrects
  the fields.
- Inventory detail quantity controls update visibly in both directions and the
  detail fact row stays in sync.
- Inventory edit now opens without Flutter debug assertions in the live mobile
  Web UI, and edited storage location data persists into the detail facts.
- Inventory edit can update reminder lead time and processing-priority tags,
  and the inventory detail view reflects both changes immediately after save.
- Inventory reminders can be disabled from the edit screen, and the detail
  view reflects the disabled state without losing the expiry date.
- Item-profile edit now saves from the live mobile Web UI and refreshes the
  detail header to the edited description without a manual browser reload.
- Item-profile edit now shows saved notes in the profile facts card, along
  with edited default unit, shelf life, reminder lead time, and storage
  location.
- Item-profile batch mode can update selected inventory storage locations, and
  both the batch card and inventory detail fact row stay in sync.
- Item-profile batch category changes update the profile-level category and
  the inventory detail fact row consistently.
- Item-profile batch consume can split a multi-quantity batch into active and
  consumed rows while keeping the active-batch count understandable.
- Item-profile batch delete can select all visible inventory batches, remove
  them together, clear selection mode, and keep profile/catalog counts in sync.
- Direct Web detail URLs now clean up late Flutter hash fragments and keep the
  copyable address bar on the app's query-route format.
- Browser Back from a searched catalog detail returns to the searched catalog
  state with the keyword preserved.
- Marking an inventory batch consumed removes it from active priority handling
  and shows it in the history tab as `已消耗`.
- History search keeps matching consumed records visible and shows a
  search-specific empty state when the keyword matches nothing.
- Restoring a consumed inventory batch from its detail page moves it out of
  History and back into active catalog and expiring views.
- Deleting a single inventory batch returns to the catalog, updates the item
  count, and leaves a friendly empty state for stale direct detail URLs.
- Empty item profiles can be deleted only after their inventory batches are
  removed, and stale profile URLs resolve to a friendly empty state.
- Shopping list checkbox moves a pending item into the purchased section.
- Purchased shopping-list items can be unchecked back into the pending section
  after a mistaken tap.
- Manual shopping-list add creates a pending item with quantity, unit, and note
  visible immediately in the mobile Web list.
- Shopping-list row editing saves quantity and note changes back to the pending
  list without stale row state.
- Shopping-list row deletion removes the pending item and lets its
  replenishment suggestion reappear.
- Purchased shopping items can be converted into inventory after confirmation,
  the catalog count updates in the live mobile Web UI, and shopping notes are
  retained as inventory batch descriptions without polluting the item-profile
  description.
- Uncategorized shopping items remain labeled `未分类` after conversion into
  catalog, item-profile, and inventory-detail surfaces.
- Catalog row cart actions add the selected item profile to the shopping list
  without navigating away, and deleting that pending item restores the
  replenishment suggestion state.
- Focused inventory cards reached from Home action tiles can add their exact
  batch to the shopping list while preserving the focused list route.
- Recipes page lists priority consumables and concrete recipe suggestions.
- AI recipe generation falls back to rule suggestions when the AI service is
  not configured, with user-facing copy and a reset action.
- AI recipe generation succeeds against a reachable local OpenAI-compatible
  endpoint, replaces the rule list with the AI result, and opens the generated
  recipe detail without mixed query/hash routing.
- Direct Web recipe URLs restore rule-generated recipe detail pages and return
  to the recipe list cleanly from the detail back action.
- Unrecoverable Web recipe detail URLs, such as stale AI-generated ids after a
  refresh, now fall back to the recipe list instead of leaving a stale detail
  route in the address bar.
- Recipe detail shows consumed inventory, missing ingredients, steps, and the
  inventory deduction action.
- Recipe favorites update from both the list and detail surfaces, and recently
  viewed recipes appear in `最近生成` without stale favorite state.
- Running a recipe deduction updates priority consumable counts in the live
  mobile Web UI and returns to the recipe list with user feedback.
- Settings self-check completed and cleaned up its temporary data, and the
  current Web UI shows the 16/16 result plus readable per-check timings.
- Settings recipe preferences save from the mobile Web UI and reload with the
  edited values still visible.
- Settings order-recognition configuration saves from the mobile Web UI,
  persists after reload without revealing the saved key, and can be cleared
  through the confirmation dialog.
- Settings order-recognition `测试配置` can validate a reachable local
  OpenAI-compatible endpoint and report `配置可用` without exposing the saved API
  key in the UI.
- Settings demo-data reset rebuilds the built-in sample data from the mobile
  Web UI while preserving user-created inventory.
- Settings inventory-table export can be triggered from the live mobile Web UI,
  and the app shows success feedback without console warnings or errors.
- Settings backup export can be triggered from the live mobile Web UI, and the
  app shows success feedback without console warnings or errors.
- Settings backup reminder appears in the live mobile Web UI after a bulk
  local import reaches the dirty-change threshold, with user-facing copy that
  explains a backup is recommended before more changes accumulate.
- Settings backup reminder can be cleared from the live mobile Web UI by using
  the reminder card's export action, and the card disappears after the app
  reports `备份已导出`.
- Settings legacy-import preview opens without probing missing optional local
  assets, so the empty bundled import file no longer causes Web asset warnings.
- Repository backup/restore tests cover pre-restore snapshots, replacement
  restore, post-restore health checks, and backup reminder clearing.
- Repository backup/restore tests now verify a backup can round-trip user
  inventory tags, ignored-reminder records, and pending shopping-list data
  across a replacement restore.
- Repository backup/restore tests now also reject incomplete or damaged backup
  files before any current data is replaced or a restore snapshot is created.
- Repository export tests now verify the user-facing inventory table uses
  readable column names, omits internal identifiers, and formats dates as
  plain calendar dates.
- Repository export tests now verify the inventory table starts with a UTF-8
  marker so spreadsheet apps can detect Chinese text more reliably.
- Repository export tests now verify inventory-table cells escape commas,
  quotes, and newlines in user-entered item names, storage locations, tags,
  and source labels.
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
- Local notification controller handoff tests now verify a notification tap
  target is stored for the app shell and consumed exactly once.
- Local notification controller tests now verify requesting permission triggers
  reminder sync only after authorization is granted, and skips scheduling when
  permission is denied.
- macOS RunnerTests now verify the native notification request builder maps
  Dart channel payloads to `inventory-<itemId>` request identifiers, preserves
  `itemId` in `userInfo`, skips malformed rows, and enforces the minimum
  trigger delay used before adding `UNNotificationRequest`s. They also verify
  native notification permission statuses map to the Flutter channel contract
  and notification tap payloads store/emit the selected inventory item id.
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
- Order-text review supports editing recognized quantities, filling missing
  units, excluding selected rows such as gifts, and confirming low-confidence
  items before batch import.
- Pasted order-text parsing now ignores standalone order/reference id lines so
  users do not have to manually exclude an obvious non-inventory row.
- Order-recognition parser tests now cover standalone reference lines in
  pasted order text while keeping normal product rows intact.
- Repository shopping-list conversion tests now verify converted shopping
  notes are retained on inventory batches and do not become item-profile
  descriptions.

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
- Filtered standalone order/reference id lines out of pasted order-text import
  so strings such as `BETA-BACKUP-001` do not appear as low-confidence
  inventory candidates.
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
- Preserved shopping-list notes when checked items are converted into
  inventory by saving the note on the inventory batch description without
  syncing it into the item-profile description.
- Unified null-category fallback copy to `未分类` across catalog cards,
  item-profile facts, and inventory-detail facts, while leaving the real
  `其他` category unchanged.
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
- Changed legacy import asset loading to consult the Flutter asset manifest
  before loading the ignored `.local` override, avoiding a Web 404 warning when
  only the bundled empty legacy file is present.
- Cleaned up Web detail route syncing so copied detail URLs are no longer set
  up to keep both the app route query and a Flutter hash route after
  navigation; later browser-history and direct-route checks verified the
  address bar stays on hash-free query routes.
- Extended the same route cleanup pattern to home priority rows, item-profile
  batch rows, and recipe detail navigation so those natural beta-user paths
  avoid mixed query/hash URLs too.
- Strengthened Web route hash cleanup with delayed retries so direct detail
  URLs also remove late Flutter hash fragments after the Navigator settles.
- Canonicalized Web route comparisons so non-ASCII generated routes, including
  Chinese AI recipe ids, are compared consistently with URL-encoded query
  routes before clearing Flutter hash fragments.
- Added recipe-detail restoration for Web route startup and history changes,
  so stable rule recipe ids can be opened from copied URLs or browser reloads.
- Added a recipe-route fallback that replaces unrecoverable detail ids with
  `/recipes`, keeping stale generated links from leaving misleading URLs.
- Added a lightweight Web loading screen that uses native system Chinese fonts,
  matches the app's warm visual style, honors reduced-motion preferences, and
  hides after Flutter's first frame to reduce the cold-start square-text flash.
- Extended the Web loading screen's first-frame delay after desktop direct-route
  testing showed CanvasKit could briefly expose square Chinese glyphs before
  fonts settled.
- Added a custom Web bootstrap that omits Flutter service-worker registration,
  unregisters stale same-origin service workers, deletes stale Flutter Cache
  Storage entries, and reloads once when the current page is still controlled
  by an old worker.
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
- Displayed non-empty item-profile notes in the profile detail facts card, so
  notes entered on the edit screen are visible after saving.
- Clarified item-profile batch category copy so the picker and success
  feedback describe the profile-level category being changed instead of
  implying only one inventory batch owns the category.
- Clarified the item-profile facts card count from `库存批次` to `使用中批次`
  because the batch list also includes consumed rows after partial
  consumption.
- Reworked remaining inventory-detail reload callbacks so edit and image
  updates refresh without returning a `Future` from `setState`.
- Reworded the history-page filtered-empty state so searching within existing
  history no longer implies there are no historical records at all.
- Reworded inventory-detail import traces so old imports show `旧版库存` rather
  than raw internal source values, and internal import batch ids are no longer
  displayed as user-facing details.
- Switched the main app shell to `MaterialApp.router` with a root Navigator
  that leaves browser history ownership to the app's query-route state, fixing
  browser Forward from a searched catalog detail back into the same detail URL.
- Reworded Settings restore/import feedback from snapshot, health-check, and
  log terminology to backup, check, detail, and record wording.
- Reworded Settings built-in check copy from acceptance wording to
  app self-check wording.
- Cleaned app self-check failure details so users see the actionable reason
  without raw exception prefixes.
- Extended the app self-check so the user-visible Settings check also verifies
  backup content includes inventory rows, tag links, reminder logs, and
  shopping-list data.
- Clarified the generic error snackbar action from `复制` to `复制详情`, keeping
  technical diagnostics out of the visible message while making the hidden copy
  action understandable.
- Reworded the backup reminder card from row/export wording to inventory-data
  backup wording, so users see why they should back up after local changes
  without spreadsheet-like implementation terms.
- Reworded data-health check messages from internal status/field names to
  inventory and profile language, so import or restore issues explain what
  needs attention without exposing raw state values.
- Reworded legacy-import and demo-reset summaries from data-row wording to
  user-facing record wording, including preview counts, import results, and
  example-data cleanup feedback.
- Reworded the order-recognition key copy from storage terminology to
  `密钥状态` / `本机安全保存` / `本机安全区域`, so Settings describes the outcome
  rather than the implementation.

## Remaining Risks

- Android local notification behavior still needs runtime validation on a
  machine with Android SDK configured. Android source-level
  manifest/channel/payload wiring and the immediate test-notification channel
  are now covered by tests, but scheduled reminder delivery, permission prompts,
  and notification-click routing still need a device or emulator.
- macOS app build and launch are now proven locally, but macOS notification
  permission, due reminder delivery, and notification-click routing still need
  targeted desktop runtime validation. The native bridge/delegate source wiring,
  immediate test-notification channel, scheduling payload builder,
  permission-status mapper, and tap payload handoff are now covered by tests,
  but system notification behavior is not fully replaceable with unit tests.
- Web app updates can still be masked by older same-origin browser cache or
  previously registered service-worker state. During Settings retesting, port
  54371 still showed older self-check wording after a rebuild, while fresh port
  54372 loaded the current build. The custom bootstrap now avoids registering a
  replacement Flutter service worker, clears stale registrations, and deletes
  stale Flutter Cache Storage entries once the current index is loaded, but
  release validation should still use a fresh origin or cache clear until the
  Web update experience is designed explicitly.
