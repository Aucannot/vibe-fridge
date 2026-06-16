# Scheme C · Warm Lifestyle UI Spec

This document captures the selected visual direction for the next vibe-fridge UI implementation.

The selected direction is **Scheme C · Warm Lifestyle**.

## Intended reference assets

When binary UI draft images are committed, use these filenames:

- `docs/ui-drafts/warm-lifestyle-refined.png`
- `docs/ui-drafts/warm-lifestyle-design-system.png`

If those image files are not present in a working branch, use this document as the textual visual spec and ask the owner to attach the PNG drafts before final implementation review.

## Product feeling

- 温暖、沉静、家庭友好
- 食材优先，而不是后台管理工具感
- 有生活方式气质，但不能牺牲录入效率
- 本地优先、数据安全、减少浪费

Suggested tagline style:

- `吃得更好，浪费更少，生活更轻松`
- `温暖、沉静、食材为先、家庭友好`

## Color tokens

Use these as initial targets. Fine-tune in Flutter if contrast requires it.

| Token | Hex | Usage |
| --- | --- | --- |
| Background / Cream | `#FAF7F1` | App scaffold background |
| Surface / Card | `#FFFFFF` | Main cards and sheets |
| Surface Warm | `#FFFDF8` | Secondary surfaces |
| Primary / Sage | `#7A8F6A` | Main CTA, selected nav, fresh status |
| Primary Dark / Olive | `#5E6F54` | Strong text/buttons |
| Lavender | `#B7A7D6` | Freshness/health accent, sparse use |
| Warning Orange | `#F4A261` | Expiry warning, 3-day urgency |
| Error Red | `#E57373` | Expired/destructive states |
| Text Primary | `#2B2A24` | Main text |
| Text Secondary | `#68645C` | Metadata and supporting text |
| Text Hint | `#9C968B` | Hints/disabled text |
| Divider | `#E8DED1` | Borders and separators |

## Shape and spacing

- Page background: warm cream, never pure white.
- Cards: large rounded rectangles, subtle border and very light shadow.
- Default card radius: 20-24.
- Inputs: rounded 14-16, soft border.
- Pills: fully rounded.
- Horizontal cards should feel tactile, like small kitchen labels.
- Bottom navigation should sit on a warm white surface with a prominent centered add button when practical.

## Typography

- Chinese UI copy should be concise and warm.
- Headline style: clear, slightly heavier, not overly playful.
- Recommended hierarchy:
  - Page title: 22-26, semibold/bold
  - Section title: 16-18, semibold
  - Body: 14-15
  - Metadata: 12-13
  - Pills: 11-12, medium/bold

## Shared components

Refresh or add reusable components around these patterns:

- Warm page header
- Hero card
- Metric card / health score card
- Expiry item card
- Action tile
- Status pill
- Quantity stepper
- Bottom CTA area
- Empty state card
- Error state card

## Screen specs

### 1. Home Dashboard

Target feeling: morning kitchen / fridge overview.

Include:

- App name: `vibe-fridge`
- Warm greeting: `早安，今天也要好好吃饭呀 ☀️`
- Optional subtle fridge/plant illustration area if achievable without bundled image assets
- Health score card: `冰箱健康评分`
- Key summary metrics:
  - 食材快要过期
  - 即将过期
  - 浪费减少 / 消耗趋势 if data exists, otherwise omit or show placeholder copy
- Horizontal `即将过期` cards showing item name, expiry status, date, thumbnail/icon
- Quick action grid:
  - 添加物品
  - 扫一扫 / 订单识别
  - 智能菜谱
  - 清理建议
- Today handling list based on expiring inventory

Use real data from `InventoryController` where possible.

### 2. Inventory List

Target feeling: clean pantry list.

Include:

- Search field
- Category chips
- Group headers such as:
  - 即将过期
  - 冷藏
  - 冷冻
  - 常温
- Item rows with:
  - icon or image placeholder
  - item name
  - category/storage metadata
  - quantity
  - expiry pill
  - chevron or tap affordance
- Preserve history view and search/category behavior.

### 3. Add Item

Target feeling: high-frequency capture flow.

Include:

- Two scan cards at top:
  - 拍照识别（食材/包装）
  - 扫一扫（条码/小票）
- Manual form:
  - 物品名称
  - 分类
  - 数量 + 单位
  - 购买日期
  - 保质期至 / 到期日期
  - 存放位置 if already supported; otherwise omit or label as future
  - 备注
- Strong sage green `保存` CTA.

Keep existing order screenshot recognition flow working.

### 4. Order Recognition Preview

Target feeling: receipt review, low stress.

Include:

- Receipt/image preview
- Source summary:
  - recognition source
  - timestamp/order id if available
  - recognized count
  - needs confirmation count
- Recognized item rows:
  - icon/thumbnail
  - name
  - quantity stepper
  - unit
  - confidence/status marker
  - include/exclude affordance
- Low confidence rows use warm orange/red highlight.
- Bottom CTA: `确认入库`.

### 5. Item Detail

Target feeling: one item as a fresh living object, not database row.

Include:

- Large hero card with item name, category, image/icon
- Quantity stepper
- Freshness timeline:
  - purchase date
  - best consumption point
  - expiry date
- Storage advice card
- Reminder setting card
- Notes
- Actions:
  - 编辑
  - 标记已消耗
  - 删除
  - 恢复 if applicable

### 6. Recipe Detail / Suggestions

Target feeling: inventory-driven cooking.

Include:

- Large food hero image area or placeholder
- Recipe title
- time, servings, calories if locally mocked or computable
- Ingredients list with available/missing status
- `优先消耗` tags for expiring ingredients
- CTA: `烹饪完成，消耗食材`

Do not implement full AI recipe backend for the UI refresh goal. Local deterministic suggestions are acceptable.

### 7. Settings

Target feeling: calm control center.

Include:

- Local data card
- Export/backup card
- VLM settings card
- Notification settings card
- About card

Keep existing settings functionality. Do not expose engineering migration
status, SDK setup state, or internal implementation progress in the app UI.

## Implementation guardrails

- Prefer reusing existing data and controllers.
- Do not add a generic TodoList feature.
- Do not add database schema unless required by an existing broken flow.
- Do not remove legacy import, VLM settings, inventory CRUD, or history.
- Do not introduce remote sync.
- Keep the app Chinese-first.

## Review checklist

- [ ] UI looks consistent with Warm Lifestyle direction.
- [ ] Home, list, add item, recognition preview, item detail, recipe, and settings are all refreshed.
- [ ] Existing inventory flows still work.
- [ ] `flutter analyze` passes.
- [ ] `flutter test` passes or failure is explained.
- [ ] PR includes screenshots for the refreshed screens.
