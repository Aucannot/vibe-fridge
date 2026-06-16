# UI Drafts

Selected direction: **Scheme C · Warm Lifestyle**.

These drafts are the visual baseline for the next Flutter UI implementation pass.
Flutter implementation tokens live in `mobile/lib/theme/app_theme.dart`, with
shared cards, page sections, empty/error/loading states, confirmation dialogs,
and action sheets in `mobile/lib/widgets/app_cards.dart`.

Files:

- `warm-lifestyle-refined.svg` — page-level direction for home, inventory list, add item, order recognition preview, item detail, and recipe detail.
- `warm-lifestyle-design-system.svg` — visual system reference for colors, cards, pills, buttons, inputs, and navigation.
- `../codex-goals/warm-lifestyle-ui-refresh.md` — Codex implementation harness.

P5.2 coverage:

| TODO screen | Verification notes |
| --- | --- |
| 首页 Dashboard | Matches today-action stats, expiring priority, and category distribution; weekly overview and quick actions continue lower in the scroll. |
| 添加物品 | Matches order/manual entry, image attachment, tags, and form hierarchy; lower form fields continue below the first fold. |
| 识别预览 | Matches editable rows, confidence, selected/importable counts, and low-confidence summary; duplicate warning appears when matching local data exists. |
| 物品目录 | Matches search, category chips, Wiki rows, batch counts, and shopping affordance; history is available via the segmented control. |
| 库存详情 | Matches quantity, reminder, edit/delete, and consume actions; image/tag/source sections render further down when present. |
| Wiki 详情 | Matches default unit, expiry, reminder, storage location, batch list, and batch-mode entry. |
| 食谱建议 | Matches priority consumables, rule/AI suggestions, favorites/recent sections, and recipe detail affordance. |
| 设置 | Matches data, backup/import, acceptance, notification, VLM, privacy, and about sections across scroll; engineering migration status is intentionally hidden from the app UI. |
| 采购清单 | Matches replenishment suggestions, grouped list states, add action, and conversion entry for checked items. |

Local screenshots may be used during review, but generated PNG captures should
not be committed by default. Keep long-lived source docs and implementation
tests in Git; leave temporary visual captures outside the repository unless a
maintainer explicitly requests them.
