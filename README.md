## vibe-fridge

> Migration note: the app is being rewritten from Kivy to Flutter. The new source lives in `mobile/`; the current Python/Kivy app remains in `app/` while migration is in progress.

### Flutter 快速启动

确认 Flutter SDK 可用：

```bash
which flutter
flutter --version
```

本分支也可以直接使用仓库内隔离安装的 SDK：

```bash
export PATH="$PWD/.tools/flutter/bin:$PATH"
flutter --version
```

安装依赖并运行 macOS 版：

```bash
cd mobile
flutter pub get
flutter run -d macos
```

运行 Android 版：

```bash
cd mobile
flutter devices
flutter run -d <android-device-id>
```

如果当前机器没有完整 Xcode 或 Android SDK，也可以先用 Web 版验证应用能启动：

```bash
cd mobile
flutter pub get
flutter build web --debug --no-wasm-dry-run
python3 -m http.server 54324 --bind 127.0.0.1 --directory build/web
```

然后访问 `http://127.0.0.1:54324/`。Web 版 SQLite 依赖 `web/sqlite3.wasm` 和 `web/sqflite_sw.js`；如果重新生成 `web/` 目录，先运行 `dart run sqflite_common_ffi_web:setup`。

质量检查：

```bash
cd mobile
flutter analyze
flutter test
```

CI 会在涉及 `mobile/**` 的 PR 和 `main`/`docs/**` 分支 push 上执行同样的 analyze/test。

### App 自验收

Flutter app 内置核心库存闭环自验收：

1. 启动 app。
2. 打开 `设置`。
3. 点击 `运行自验收`。

自验收会创建临时库存，验证创建、Wiki 关联、今天要处理聚合、提醒日志去重/忽略、数量更新、批量改位置/分类、标记消耗、恢复、删除、清理流程和数据健康检查；结束后会删除自身测试数据。

自验收也会基于临时库存生成一条本地规则食谱建议，确保“临期库存 -> 食谱建议”的入口没有退回占位态。

自验收还会创建一条临时采购清单，验证“采购建议 -> 勾选已买到 -> 转为库存”的补货闭环。

### Flutter 数据安全

Flutter SQLite 使用显式 schema migration，当前版本是 `AppDatabase.schemaVersion = 4`。数据层已提供：

- 完整 JSON 备份 payload：`InventoryRepository.exportBackup()`
- 人工可读库存 CSV：`InventoryRepository.exportInventoryCsv()`
- 恢复前本地快照：`InventoryRepository.createBackupSnapshot()`
- 事务内恢复与健康检查：`InventoryRepository.restoreBackup()`
- 数据不变量检查：`InventoryRepository.checkDataHealth()`

设置页已经提供 `导出备份`、`恢复备份` 和 `导出库存 CSV`。恢复备份前会自动创建本地快照。

首次 legacy 导入或累计大量本地修改后，设置页会提示导出 JSON 备份。成功导出备份后，这个提醒会自动清除。

### Legacy 数据导入

旧 Python/Kivy SQLite 数据库不会被 Flutter app 直接修改。要生成 Flutter 可导入的 JSON：

```bash
python tools/export_legacy_inventory.py \
  --source data/vibe_fridge.db \
  --output mobile/assets/import/legacy_inventory.local.json
```

然后启动 Flutter app，在 `设置` 中点击 `预览并导入 legacy_inventory.json`。导入前会显示分类、Wiki、库存、标签数量，以及按 id、名称、时间戳判断的冲突处理结果；确认后才写入本地数据库。对真实数据迁移可勾选“导入前清空示例 Wiki/库存”。本地 `.local.json` 文件不会提交到 Git。

### VLM 订单截图识别

在 Flutter app 的 `设置` 页填写：

- Endpoint：OpenAI-compatible chat completions endpoint。
- Model：支持图片输入的 VLM 模型。
- API Key：保存在系统安全存储，不写入 SharedPreferences。

可以先点击 `测试配置` 验证 endpoint、model 和 key。失败时会区分配置、网络、鉴权、图片格式、服务端和返回格式问题；设置页也支持清空配置和恢复默认配置。

之后进入 `添加` -> `订单识别`，可从相册、文件或相机导入订单图片，也可以粘贴订单文本。预览页可逐项编辑识别结果，低置信度条目需要确认，同订单/商品/购买日期的重复项会跳过，导入完成后会显示新增、跳过和需要手动处理的 summary。桌面平台如果没有系统相机拍摄 UI，会提示改用相册或文件导入。

### 食谱消耗建议

Flutter app 的 `食谱` 页已接入本地规则推荐：先按过期日、数量、分类展示优先消耗食材，再基于当前库存生成 3-5 个菜谱建议。详情页会列出将消耗的库存、缺失食材、步骤、预计耗时，并支持“做这道菜并扣减库存”。收藏和最近生成会保留在当前 app 会话中。

食谱页也支持通过已配置的 VLM endpoint 生成 AI 食谱。设置页可保存口味、忌口、厨具、人数和烹饪时间；AI 返回会解析成同一套食谱结构，失败时自动回退到本地规则建议。

### 采购与补货

`物品` 页新增 `采购` 分段。页面会根据低库存、已用完和常买物品生成补货建议；用户也可以从物品目录或历史记录把条目加入采购清单。

采购清单支持按分类分组、勾选已买到、调整数量、记录单位和备注。勾选后的条目可以一键入库，入库仍复用现有 Wiki + 库存创建流程。

### 库存图片附件

手动添加和编辑库存时可以从相册、文件或相机添加包装、小票、标签照片。图片会复制到 app 文档目录的 `attachments/inventory/` 下，库存详情页会显示本地预览和保存路径。

### 库存标签

手动添加和编辑库存时可以勾选 `临期优先`、`已开封`、`囤货`、`常用`、`易浪费` 等预设标签。标签会写入本地 `tags` / `item_tags` 表，并在库存详情页展示。

### 批次策略

同名且同过期日的库存不会自动合并：它们共享同一个 Wiki 条目，但每次入库仍保留为独立批次，以便追踪包装照片、订单来源、标签、存放位置和后续编辑。用户可以在具体批次上调整数量或标记消耗。

### 批量操作

在 Wiki 详情页的库存批次区域点击 `批量`，或长按某个批次，可以选择多条库存记录并批量删除、修改存放位置、修改 Wiki 分类，或对选中的使用中批次各消耗 1 件。

### 提醒处理

首页 `今天要处理` 会聚合已过期、今日到期和提醒到期的库存。条目支持 `稍后` 和 `忽略`，当天会从列表隐藏；底层 `reminder_logs` 也会阻止同一物品同一提醒类型在同一天重复记录。

### FAQ

- `flutter: command not found`：先安装 Flutter SDK，并把 `<flutter-sdk>/bin` 加入 PATH。
- macOS 无可用设备：执行 `flutter config --enable-macos-desktop` 后重试。
- Android 无设备：先安装 Android SDK，启动模拟器或连接真机，再运行 `flutter devices`。
- 本机缺完整 Xcode/Android SDK：先用 `flutter build web --debug --no-wasm-dry-run` 加静态服务做启动验证。
- 依赖解析失败：在 `mobile/` 下重新运行 `flutter pub get`。
- VLM 识别失败：检查 endpoint/model/key 是否匹配，确认所选模型支持图片输入。

See `docs/flutter_migration.md` for migration details.

### 🚀 快速开始

#### 1. 克隆代码仓库

```bash
git clone YOUR_GITHUB_REPO_URL
cd vibe-fridge
```

#### 2. 创建并激活虚拟环境（推荐）

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows（PowerShell）：

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 启动应用

```bash
python -m app.main
```

或直接：

```bash
python app/main.py
```

启动后会打开一个 360×640 的 KivyMD 窗口，它就是 vibe-fridge 的主界面。


> 说明：目前功能还在快速迭代中，这里只提供最基本的环境配置和启动方式，后续稳定后再补充详细文档。
