# UI Drafts

Selected direction: **Scheme C · Warm Lifestyle**.

These drafts are the visual baseline for the next Flutter UI implementation pass.
Flutter implementation tokens live in `mobile/lib/theme/app_theme.dart`, with
shared cards, page sections, empty/error/loading states, confirmation dialogs,
and action sheets in `mobile/lib/widgets/app_cards.dart`.

Files:

- `warm-lifestyle-refined.svg` — page-level direction for home, inventory list, add item, order recognition preview, item detail, and recipe detail.
- `warm-lifestyle-design-system.svg` — visual system reference for colors, cards, pills, buttons, inputs, and navigation.
- `design-system.png` — exported design system draft used by TODO P5.1.
- `dashboard.png` — concrete home dashboard draft for stats, today-action reminders, expiring priority, and category distribution.
- `add-item.png` — concrete add-item draft for manual entry, order recognition entry, fields, image attachment, tags, and save action.
- `order-import-review.png` — concrete order import review screen draft for editable rows, low-confidence confirmation, duplicate warnings, and import summary behavior.
- `items-catalog.png` — concrete item catalog draft for search, category rail, Wiki rows, batch counts, tags, and history affordances.
- `item-detail.png` — concrete inventory detail draft for quantity controls, reminder settings, image/source metadata, tags, edit, and consume actions.
- `wiki-detail.png` — concrete Wiki detail draft for default unit, default expiry, default reminder, storage location, inventory batches, and history insight.
- `recipes-home.png` — concrete recipes home draft for priority consumables, rule suggestions, favorites, recent suggestions, and recipe detail affordances.
- `settings.png` — concrete settings draft for local data, notifications, acceptance checks, VLM configuration, privacy, and about information.
- `shopping-list.png` — concrete shopping list draft for replenishment suggestions, grouped purchase items, bought-state checkboxes, and inventory conversion.
- `implementation/dashboard-web.png` — Flutter Web implementation screenshot for the home dashboard.
- `implementation/add-item-web.png` — Flutter Web implementation screenshot for the add-item screen.
- `implementation/order-import-review-web.png` — Flutter Web implementation screenshot for order import review.
- `implementation/items-catalog-web.png` — Flutter Web implementation screenshot for the item catalog.
- `implementation/item-detail-web.png` — Flutter Web implementation screenshot for inventory detail.
- `implementation/wiki-detail-web.png` — Flutter Web implementation screenshot for Wiki detail.
- `implementation/recipes-home-web.png` — Flutter Web implementation screenshot for recipes.
- `implementation/settings-web.png` — Flutter Web implementation screenshot for settings.
- `implementation/shopping-list-web.png` — Flutter Web implementation screenshot for the shopping list.
- `../codex-goals/warm-lifestyle-ui-refresh.md` — Codex implementation harness.

P5.2 coverage:

| TODO screen | UI draft | Implementation screenshot | Difference notes |
| --- | --- | --- | --- |
| 首页 Dashboard | `dashboard.png` | `implementation/dashboard-web.png` | Matches today-action stats, expiring priority, and category distribution; weekly overview and quick actions continue lower in the scroll. |
| 添加物品 | `add-item.png` | `implementation/add-item-web.png` | Matches order/manual entry, image attachment, tags, and form hierarchy; lower form fields continue below the first fold. |
| 识别预览 | `order-import-review.png` | `implementation/order-import-review-web.png` | Matches editable rows, confidence, selected/importable counts, and low-confidence summary; duplicate warning appears when matching local data exists. |
| 物品目录 | `items-catalog.png` | `implementation/items-catalog-web.png` | Matches search, category chips, Wiki rows, batch counts, and shopping affordance; history is available via the segmented control. |
| 库存详情 | `item-detail.png` | `implementation/item-detail-web.png` | Matches quantity, reminder, edit/delete, and consume actions; image/tag/source sections render further down when present. |
| Wiki 详情 | `wiki-detail.png` | `implementation/wiki-detail-web.png` | Matches default unit, expiry, reminder, storage location, batch list, and batch-mode entry. |
| 食谱建议 | `recipes-home.png` | `implementation/recipes-home-web.png` | Matches priority consumables, rule/AI suggestions, favorites/recent sections, and recipe detail affordance. |
| 设置 | `settings.png` | `implementation/settings-web.png` | Matches data, backup/import, acceptance, notification, VLM, privacy, and about sections across scroll; engineering migration status is intentionally hidden from the app UI. |
| 采购清单 | `shopping-list.png` | `implementation/shopping-list-web.png` | Matches replenishment suggestions, grouped list states, add action, and conversion entry for checked items. |

Screenshots were captured from the Flutter Web debug build at a 393x852
mobile viewport because the local machine lacks full Xcode and Android SDK
device targets. Native screenshots should be refreshed during Android/macOS
release validation.
