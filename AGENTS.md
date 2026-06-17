# AGENTS.md

This file provides guidance to Codex when working with code in this repository.

## 项目概述

**vibe-fridge** 是一个 Flutter 跨平台库存管理应用，核心目标是用「物品资料 + 库存批次」管理家中物品，并提供过期提醒、采购建议、食谱建议、订单识别和本地备份能力。

当前主要实现位于 `mobile/`。早期 Python/Kivy 版本只作为迁移来源和历史参考；日常开发、测试和构建都以 Flutter 代码为准。

## 当前技术栈

| 组件 | 当前实现 |
|------|----------|
| UI | Flutter + Material 3 |
| 状态协调 | `InventoryController` |
| 本地数据库 | SQLite via `sqflite` |
| Web SQLite | `sqflite_common_ffi_web` + `web/sqlite3.wasm` |
| 安全存储 | `flutter_secure_storage` |
| 偏好存储 | `shared_preferences` |
| 文件导入导出 | `file_selector` |
| 图片来源 | `image_picker` + 本地图片存储 |
| 网络请求 | `http`，仅 VLM 订单识别和 AI 食谱动作使用 |
| 本地通知 | Flutter method channel + Android/macOS 原生实现 |
| 测试 | `flutter_test` + `sqflite_common_ffi` |

## 当前目录结构

```text
vibe-fridge/
├── mobile/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── data/
│   │   │   ├── app_database.dart
│   │   │   ├── inventory_controller.dart
│   │   │   ├── inventory_repository.dart
│   │   │   ├── local_image_store.dart
│   │   │   ├── local_notification_service.dart
│   │   │   ├── vlm_order_service.dart
│   │   │   ├── ai_recipe_service.dart
│   │   │   └── acceptance_test_service.dart
│   │   ├── models/
│   │   ├── screens/
│   │   ├── theme/
│   │   ├── utils/
│   │   └── widgets/
│   ├── test/
│   ├── assets/
│   ├── android/
│   ├── macos/
│   ├── web/
│   └── pubspec.yaml
├── docs/
├── tools/
└── AGENTS.md
```

## 领域模型

代码中仍使用 `ItemWiki` 命名表达「物品资料」，但用户界面应优先使用「物品资料」这个产品语言。

1. **ItemWikiCategory（分类）**
   - 食品、日用品、化妆品、药品、其他等分类。
   - 对应图标、颜色和排序。

2. **ItemWiki（物品资料）**
   - 某种物品的类定义。
   - 保存名称、描述、分类、默认单位、建议保质期、默认提醒提前天数、存放位置、备注、图片路径等。
   - 一个物品资料可以关联多条库存批次。

3. **InventoryItem / Item（库存批次）**
   - 某次实际持有的库存。
   - 保存数量、单位、购买日期、过期日期、提醒日期、提醒开关、状态、标签、图片路径、来源订单等。
   - 状态包括 `active`、`expired`、`consumed`。

4. **RegisteredItem**
   - 物品目录里的聚合视图。
   - 以物品资料为主，合并展示关联库存批次、总数量、最近过期信息等。

5. **ShoppingListItem**
   - 采购清单记录。
   - 可由低库存/常买建议生成，也可勾选后转换回库存批次。

## 主要页面

| 页面 | 文件 | 说明 |
|------|------|------|
| App shell | `mobile/lib/screens/app_shell.dart` | 底部导航、路由协调、深链参数处理 |
| 首页 | `home_screen.dart` | 统计、今天要处理、即将过期、采购/食谱入口 |
| 物品 | `items_screen.dart` | 物品目录、历史、采购清单、分类筛选 |
| 添加物品 | `add_item_screen.dart` | 手动添加、拍照/相册、订单识别入口 |
| 订单复核 | `order_import_review_screen.dart` | 识别结果复核并批量入库 |
| 库存详情 | `item_detail_screen.dart` | 单条库存批次详情、消耗/恢复/删除、图片 |
| 库存编辑 | `item_edit_screen.dart` | 单条库存批次编辑 |
| 物品资料详情 | `item_wiki_detail_screen.dart` | 物品资料与所有关联库存 |
| 物品资料编辑 | `item_wiki_edit_screen.dart` | 默认单位、提醒、分类等资料编辑 |
| 食谱 | `recipes_screen.dart` | 本地规则食谱和 AI 食谱建议 |
| 设置 | `settings_screen.dart` | 备份、通知、VLM、食谱偏好、自验收 |

## 关键服务

- `AppDatabase`
  - 负责 SQLite 打开、建表、迁移、索引、默认数据。
  - schema 版本由 `AppDatabase.schemaVersion` 管理。

- `InventoryRepository`
  - 主要数据访问层。
  - 覆盖库存、物品资料、分类、标签、提醒日志、购物清单、备份、旧版库存导入、数据健康检查。

- `InventoryController`
  - UI 与 repository 之间的协调层。
  - 维护分类、统计、通知权限、备份提醒等页面状态。

- `LocalImageStore`
  - 管理用户拍摄、相册选择、文件选择得到的物品图片。

- `LocalNotificationService`
  - 通过 platform channel 调用 Android/macOS 原生通知能力。

- `VlmOrderService`
  - 调用 OpenAI-compatible VLM endpoint 识别订单截图或订单文本。

- `AiRecipeService` / `RecipeSuggestionService`
  - AI 食谱请求和本地规则食谱建议。

- `AcceptanceTestService`
  - 设置页里的应用自验收流程。
  - 用临时数据验证核心 CRUD、提醒、购物清单、食谱建议和数据健康检查。

## 本地运行与验证

仓库自带 Flutter SDK 时优先使用：

```bash
export PATH="$PWD/.tools/flutter/bin:$PATH"
cd mobile
flutter pub get
flutter analyze
flutter test
flutter run -d macos
```

当前 Codex 环境里也可以直接使用绝对路径：

```bash
cd mobile
HOME=/private/tmp/vibe-fridge-flutter-home ../.tools/flutter/bin/flutter analyze
HOME=/private/tmp/vibe-fridge-flutter-home ../.tools/flutter/bin/flutter test
HOME=/private/tmp/vibe-fridge-flutter-home ../.tools/flutter/bin/flutter build web --debug --no-wasm-dry-run
```

Web 本地预览：

```bash
cd mobile
flutter build web --debug --no-wasm-dry-run
python3 -m http.server 54324 --bind 127.0.0.1 --directory build/web
```

打开 `http://127.0.0.1:54324/`。

如果 `web/` 目录被重新生成，需确保 Web SQLite 资产存在：

```bash
cd mobile
dart run sqflite_common_ffi_web:setup
```

## 数据库与迁移

- Flutter 应用使用自己的 SQLite 数据库，不直接写旧 Python 数据库。
- schema 迁移集中在 `mobile/lib/data/app_database.dart`。
- 迁移测试在 `mobile/test/app_database_migration_test.dart`。
- 数据健康检查由 `InventoryRepository.checkDataHealth()` 提供，覆盖数量、状态、日期、提醒顺序、关联完整性、消耗状态等。
- 设置页的备份/恢复最终调用 repository 的 JSON-ready backup payload，但 UI 文案应使用「备份」「库存表格」等用户语言，不暴露 JSON、SQLite、数据库等实现细节。

## 用户界面文案规范

- 不要在普通用户界面暴露 `数据库`、`SQLite`、`迁移状态`、`legacy`、`Wiki`、`id`、`ISO-8601` 等工程术语。
- `ItemWiki` 在代码中保留为领域名，但界面文案使用「物品资料」。
- 旧数据导入面向用户时使用「旧版库存」。
- CSV 面向用户时使用「库存表格」。
- JSON backup 面向用户时使用「备份」。
- 设置页不展示数据库类型、迁移状态或底层存储实现。
- 错误信息应说明用户能理解和处理的问题，必要的技术详情放入可复制错误详情或日志中。

## 网络与隐私

- 默认库存、目录、采购清单、备份、提醒和本地规则食谱均应离线可用。
- 只有用户主动触发 VLM 订单识别或 AI 食谱时，才可向用户配置的 endpoint 发送请求。
- API key 通过 `flutter_secure_storage` 保存。
- 订单截图、订单文本和库存上下文只能在用户主动触发相关 AI 动作时发送。
- 新增网络能力时必须明确入口、触发条件、用户可见文案和测试覆盖。

## 本地通知

- Flutter 侧入口在 `LocalNotificationService`。
- Android 通过 `vibe_fridge/local_notifications` method channel 调用 `AlarmManager` 和通知 receiver。
- macOS 通过 `UNUserNotificationCenter`。
- 通知点击会把库存 `itemId` 返回 Flutter，并打开库存详情页。
- 修改通知相关代码后，至少跑 `flutter analyze` 和相关 repository tests；平台行为还需要真机或桌面运行验证。

## 测试规范

- 长期保留的测试放在 `mobile/test/`，必须服务于 CI、回归验证或长期质量保障。
- 一次性测试代码、临时调试脚本、探索性验证代码无需上传至仓库；如果确实需要保留，应沉淀为长期 CI 测试或正式工具。
- 不要提交只为当前调试服务、没有长期维护价值的测试文件。
- 对 repository、数据库迁移、解析器、AI fallback、通知 payload、备份恢复等共享逻辑的修改，应优先补充或更新长期测试。
- UI 文案调整至少做 targeted grep；功能性 UI 调整应配合 widget test、浏览器烟测或手动运行说明。

## 代码规范

- 保持 Flutter/Dart 现有分层：UI screen 不直接写 SQL；共享数据逻辑放入 repository/controller/service。
- 优先使用现有 widget、theme、spacing 和 helper，不为单个页面发明孤立样式体系。
- 数据库 schema 变化必须通过 migration 和测试覆盖，不直接假设用户是新库。
- 文件、图片、备份等本地 I/O 通过已有 store/service 封装，避免在 screen 内散落路径处理。
- 手动编辑文件使用 `apply_patch`。
- 提交前运行与改动范围匹配的验证；常规 Flutter 改动至少跑 `flutter analyze`，数据层改动跑 `flutter test`。
- 完成一个功能并验证完善后，需要 commit 并 push 到当前工作分支，保持良好的版本管理。
- 工作区可能存在其他人的未提交改动；只 stage/commit 本次任务相关文件，不回滚无关改动。

## 版本管理规范

- 开始任务先确认当前分支。
- 禁止向 `main` 分支直接 commit；所有改动必须在工作分支提交，并通过 PR 合并到 `main`。
- 提交前查看 `git status --short` 和相关 `git diff`。
- 只 stage 本次任务相关文件。
- commit message 使用简洁、可追踪的英文祈使句，例如 `Update agent guidance for Flutter app`。
- 功能完成并验证通过后推送当前分支。
- 如果验证失败，不要为了提交而掩盖失败；先修复或在交付说明中明确阻塞点。

## 发布与平台注意事项

- Android release 签名使用 `mobile/android/key.properties`，真实 key 和 keystore 不提交。
- macOS 分发证书、notarization 凭据和导出配置不要提交真实秘密。
- 图标资源已在 Android mipmap 和 macOS AppIcon 中维护，源图在 `mobile/assets/brand/app_icon.png`。
- Android/macOS 权限文案需要和实际功能匹配，尤其是相机、相册、通知、网络。

## Codex 工作约定

- 默认以 `mobile/` Flutter 应用为当前产品实现。
- 当用户反馈「app 内不该出现某词」时，同时检查设置页、首页、详情页、弹窗、snackbar、错误信息和导入日志。
- 对用户可见功能不要只改代码路径，也要验证可运行状态。
- 若本地浏览器服务没有刷新到最新 build，不要把浏览器旧页面当作最终视觉验证。
- 文档改动通常不需要跑完整 Flutter 测试，但如果文档同步了测试或命令约定，应至少检查格式和 diff。
