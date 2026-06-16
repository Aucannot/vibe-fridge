# UX Test Findings - 2026-06-16

Scope: exploratory UX testing against the Flutter Web debug build opened in the
in-app browser at `http://127.0.0.1:54324/`.

Viewport: mobile-sized in-app browser viewport.

Focus: high-frequency app flows where the UI visually suggests an action, but
the app either does not navigate, does not update state, or does not provide
enough feedback.

## Summary

The core visual refresh is in place, but several high-signal surfaces still act
like static dashboards. The biggest gap is on the home screen: status chips,
summary counts, and priority item rows look like entry points but do not open a
filtered list or detail page. The shopping list also has a blocking interaction
bug where a pending purchase checkbox cannot be toggled, which breaks the
purchase-to-inventory loop.

## Fix Status

Updated: 2026-06-16.

| ID | Status | Resolution |
| --- | --- | --- |
| UX-001 | Fixed | Home status chips and the top count now request focused item lists for expired, due-today, reminder-due, and cleanup inventory. |
| UX-002 | Fixed | Home expiring-priority rows now open the inventory batch detail screen and refresh on return. |
| UX-003 | Fixed | Re-entering the Home tab recreates the Home screen so the primary summary starts at the top. |
| UX-004 | Fixed | Reminder snooze/ignore actions refresh the animated Home screen state and show contextual feedback after completion. |
| UX-005 | Fixed | Home `清理建议` now lands on a cleanup-focused inventory list instead of the default catalog. |
| UX-006 | Fixed | Catalog `即将过期` mini cards now open the corresponding inventory batch detail. |
| UX-007 | Fixed | Shopping rows now expose a larger checkbox target and row-label tap target; checking items moves them into the purchased section through the existing controller refresh. |
| UX-008 | Fixed | Shopping quantity stepper controls now use stable 44px tap targets and preserve controller-driven quantity refresh. |
| UX-009 | Fixed | Flutter Web now reflects app state in query URL parameters, for example `?route=items&focus=cleanup` and `?route=items&view=shopping`. Query parameters are used instead of hash routes because Flutter Web reserves hash routing internally. |
| UX-010 | Fixed | Wiki detail async refresh and batch actions now guard `mounted` before post-await `setState` calls. |
| UX-011 | Fixed | `StatusPill` text now flexes and ellipsizes inside constrained rows to avoid mobile `RenderFlex` overflow. |

Verification:

- `flutter analyze`: passed.
- `flutter test`: passed.
- `flutter build web --debug --no-wasm-dry-run`: passed.
- Browser smoke check against a fresh `mobile/build/web` server: `?route=home`, `?route=items&focus=expired`, `?route=items&focus=cleanup`, `?route=items&view=shopping`, `?route=add`, and `?route=recipes` all preserved URL state with no new console errors on the verified build.

## Findings

| ID | Severity | Area | Reproduction | Observed | Expected |
| --- | --- | --- | --- | --- | --- |
| UX-001 | High | Home dashboard | Open 首页, tap `已过期`, `今日到期`, `提醒到期`, and the top-right `2 件` badge. | No navigation, no filter, no visual state change, URL remains `/`. | Each stat should open a corresponding filtered inventory/reminder list, or clearly expose that it is only informational. |
| UX-002 | High | Home dashboard | Open 首页, tap the `临期优先` rows for `面包` and `鲜牛奶`. | Rows do not open item detail, Wiki detail, or a filtered expiring list. | Tapping an urgent item should go directly to its batch/detail page, or to a filtered expiring list when multiple batches exist. |
| UX-003 | Medium | Home navigation state | Scroll 首页 to the middle, switch to another tab, then tap 首页 again. | 首页 returns to the previous mid-scroll position instead of the top summary. | For a primary tab re-entry, return to the top or make re-tapping the active tab scroll to top. |
| UX-004 | High | Today actions | In 首页 `今天要处理`, tap `稍后` or `忽略` on a reminder card. | A snackbar appears, but the card remains in the list and the `2 项` count does not change. | The card should be removed, dimmed, moved to a snoozed/ignored state, and the count should update immediately. Include undo if needed. |
| UX-005 | Medium | Home quick action | Tap 首页 `清理建议`. | It lands on the default item catalog view. | It should land on a cleanup-specific view, such as expiring/history-filtered inventory, or the label should be changed to match the destination. |
| UX-006 | High | Item catalog | Open 物品目录, tap the `即将过期` mini cards for `面包` or `鲜牛奶`. | Only a touch/ripple-like visual change occurs; no detail page or filter opens. | These cards should open the relevant item/batch detail, or a focused expiring inventory list. |
| UX-007 | High | Shopping list | From 物品目录, tap a row cart icon to add an item to 采购清单. Open 采购, tap the pending checkbox. | The checkbox does not toggle after repeated taps. The item stays in `待采购`, and `已买到` remains `0`. | Checking the box should move the item into `已买到`, update counts, and reveal/enable the inventory conversion path. |
| UX-008 | Medium | Shopping list | In 采购清单, tap `+` in the pending item quantity stepper. | The button highlights, but the quantity remains `1`. | The quantity should increment immediately and persist. |
| UX-009 | Medium | Web navigation | Navigate between 首页, 添加, 食谱, 物品详情, Wiki 详情, and 采购. | The browser URL stays `http://127.0.0.1:54324/` for all screens. | For the Web build, route state should be reflected in the URL, or browser back/deep-link limitations should be accepted and documented. |
| UX-010 | High | Runtime stability | Open Wiki detail and move between Wiki/detail/catalog flows, then inspect browser console. | Console records repeated `ItemWikiDetailScreenState.setState` errors. | Async callbacks in detail screens should guard `mounted` before `setState` after awaits/navigation. |
| UX-011 | High | Mobile layout | Inspect browser console after navigating item/Wiki/detail flows on the mobile viewport. | Flutter reports `A RenderFlex overflowed by 21 pixels on the right` inside `StatusPill`. | Status pills should wrap, truncate, or flex safely without rendering overflow errors. |

## Passing Checks Observed

- 首页 `添加物品` quick action opens the add-item screen.
- 首页 `订单识别` quick action opens the add-item screen with the order-recognition module visible in the first viewport.
- 首页 `智能菜谱` quick action opens 食谱.
- 物品目录 Wiki rows open Wiki detail.
- Wiki detail batch rows open inventory detail.
- Inventory detail quantity `+` and `-` update the quantity visibly.
- Catalog row cart icon adds an item to the shopping list and shows snackbar feedback.
- Shopping item overflow menu opens and exposes `编辑` / `删除`.

## Notes

- This test pass added `感冒药` to the shopping list to verify the catalog-to-shopping flow.
- Console errors were read from the in-app browser after reproducing the flows above; older and newly timestamped errors were both present.
