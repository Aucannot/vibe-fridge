# vibe-fridge UI Design System

`app/ui/theme/design_tokens.py` 是当前主题源。这个文档负责解释它背后的设计意图，以及后续页面改造时应该怎么用。

## 1. 产品气质

vibe-fridge 不是通用 SaaS，也不是强装饰型生活方式 App。它更适合以下气质：

- 新鲜感：联想到冷藏、保鲜、整洁和可控。
- 工具感：信息清晰、层级稳定、能快速录入和扫描。
- 家庭感：不能太冷硬，需要一点温和和日常感。
- 中文优先：信息密度较高时仍要保持可读性。

设计关键词：

- `fresh utility`
- `clean refrigeration`
- `friendly data density`
- `calm confidence`

应避免：

- 泛用紫粉渐变 SaaS 风格
- 过重阴影和过度玻璃拟态
- 全屏高饱和色块
- 只靠颜色表达状态，不给文字提示

## 2. 配色系统

### 2.1 角色定义

| 角色 | Token | Hex | 用途 |
|---|---|---|---|
| 主色 | `primary` | `#1B8B7A` | 主按钮、关键统计、选中态、品牌识别 |
| 冷辅助色 | `secondary` | `#4E7BC7` | 信息标签、冷藏/日期/辅助导航 |
| 暖强调色 | `tertiary` / `accent` | `#E49A41` | 食谱、提醒入口、轻强调区 |
| 成功 | `success` | `#2E9F6B` | 正常库存、已妥善记录、完成态 |
| 警告 | `warning` | `#D98E04` | 即将过期、需要关注 |
| 错误 | `error` | `#D95C5C` | 已过期、删除、失败反馈 |
| 页面背景 | `background` | `#F4F8F7` | 整页底色 |
| 主表面 | `surface` | `#FFFFFF` | 卡片、弹层、表单区块 |
| 柔和表面 | `surface_variant` | `#ECF3F1` | 次级容器、筛选条、占位态 |
| 文本主色 | `text_primary` | `#1F2624` | 标题、主要内容 |
| 文本次色 | `text_secondary` | `#46514E` | 说明文字、字段名 |
| 文本弱化 | `text_hint` | `#7C8B87` | 占位、辅助信息 |

### 2.2 用法规则

- `primary` 只给当前页面最重要的动作和最重要的数字，不要在一个屏幕里同时刷满主色。
- `secondary` 代表冷静信息，不和 `warning` 混用。日期、冷藏位置、说明型状态优先使用它。
- `accent` 是暖色补充，不承担危险态，主要用于“食谱”“建议”“轻提醒”。
- 状态类背景优先用 `*_container`，不要直接大面积铺高饱和实色。
- 页面背景始终保持浅色，卡片通过白色表面和轻边框建立层次，而不是靠深重阴影。

### 2.3 页面分布建议

| 区域 | 推荐色 |
|---|---|
| 首页总览统计 | `primary`, `warning`, `error` |
| 物品列表信息点 | `secondary`, `text_secondary` |
| 表单卡片 | `surface`, `divider`, `text_primary` |
| 空状态 / 占位 | `surface_variant`, `text_hint` |
| 即将过期提示 | `warning_container` + `warning_dark` |
| 已过期提示 | `error_container` + `error_dark` |

## 3. 字体规范

### 3.1 字体策略

应用是中文优先，字体策略应以系统中文字体为主，英数信息保持中性和清楚。

| 角色 | 建议字体 |
|---|---|
| 主 UI 字体 | `ChineseFont`，由运行时映射到系统中文字体 |
| macOS 优先 | PingFang SC / STHeiti / Songti |
| Windows 优先 | Microsoft YaHei |
| Linux 优先 | Noto Sans CJK / WenQuanYi |
| 数字与英文字段 | `Roboto` |

### 3.2 字号层级

直接使用 `design_tokens.py` 中的类型角色：

| 场景 | Token | 建议 |
|---|---|---|
| 页面标题 | `headline_small` / `title_large` | 首页、详情页顶部标题 |
| 卡片主数字 | `headline_medium` / `headline_small` | 库存总数、过期数 |
| 区块标题 | `title_medium` | 表单卡片标题、列表分组标题 |
| 正文 | `body_large` / `body_medium` | 名称、描述、字段内容 |
| 辅助信息 | `label_large` / `label_medium` | 标签、日期、单位、状态说明 |

### 3.3 字重和排版规则

- 页面标题和核心数字允许 `bold`，其他区域优先常规字重，避免整屏都很重。
- 中文正文尽量保持 `14dp` 或 `16dp`，不要把重要信息压到 `12dp` 以下。
- 数字类信息尽量稳定对齐，库存数量、日期、统计值使用更规整的间距。
- 一张卡片里最多保留一个强标题和一个主数字，避免三级标题叠加。

## 4. 卡片规范

当前代码里卡片半径和阴影比较分散，后续统一收敛到 4 类。

### 4.1 Hero Card

对应 token：`DESIGN_TOKENS["card"]["hero"]`

适用：

- 首页统计卡
- 关键汇总信息
- 需要一眼读取的核心数字

规范：

- 圆角 `20`
- 内边距 `20`
- 白色表面
- 轻阴影，不加描边
- 左上可有浅色图标底块，使用 `primary_container` / `secondary_container`

### 4.2 Section Card

对应 token：`DESIGN_TOKENS["card"]["section"]`

适用：

- AddItemScreen 表单分组
- Wiki 编辑页分组
- 详情页的信息区块

规范：

- 圆角 `16`
- 内边距 `16`
- `1px` 轻边框
- 阴影只做弱分层，不做悬浮感
- 标题在上，字段按从高频到低频排列

### 4.3 List Card

对应 token：`DESIGN_TOKENS["card"]["list"]`

适用：

- ItemsScreen 中的物品列表
- Wiki 条目卡
- 可点击结果项

规范：

- 圆角 `14`
- 内边距 `14`
- 轻边框优先于阴影
- 选中态通过 `primary_container`、边框或小色条强调
- 按压只做轻微缩放，不能跳动明显

### 4.4 Status Card

对应 token：`DESIGN_TOKENS["card"]["status"]`

适用：

- “即将过期”“已过期”“库存正常”提示块
- 小型信息状态条

规范：

- 圆角 `14`
- 使用 `success_container` / `warning_container` / `error_container`
- 必须配合文案或图标，不只给颜色
- 不要叠加额外阴影

## 5. 组件行为规则

- 触控目标至少 `44dp`
- 页面只保留一个最强 CTA
- 选中态优先用“背景容器色 + 深色文字”，而不是纯色实底
- 卡片 hover / press 反馈保持轻量，推荐缩放到 `0.98`
- 列表项不要同时使用粗描边、重阴影、强底色三种强调手段

## 6. 页面映射建议

| 页面 | 推荐卡片类型 | 说明 |
|---|---|---|
| `MainScreen` | `hero` + `list` | 顶部统计用 hero，库存列表用 list |
| `AddItemScreen` | `section` | 基本信息、数量、日期、选项分组统一成表单卡 |
| `ItemsScreen` | `list` | 列表项收敛成统一信息密度 |
| `ItemDetailScreen` | `section` + `status` | 详情字段分组 + 状态提示 |
| `ItemWikiEditScreen` | `section` | 编辑流以表单卡为核心 |

## 7. 实施优先级

下一步如果继续做界面改造，建议顺序如下：

1. 先统一 `AddItemScreen` 的表单卡和按钮层级。
2. 再统一 `MainScreen` / `ItemsScreen` 的统计卡与列表卡。
3. 最后收敛详情页和 Wiki 编辑页的卡片半径、边框和状态色。
