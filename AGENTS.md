# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## 项目概述 (Project Overview)

**"vibe-fridge"** 是一个基于 Python 的移动端应用，采用 Wiki 体系管理物品，结合了库存管理和过期提醒功能。项目使用 Conda 虚拟环境进行依赖管理（环境名：kivy）。

### 核心架构：Wiki 体系

项目采用双层架构设计：

1. **ItemWiki（物品 Wiki）**：物品的「类定义」
   - 存储物品的通用属性：名称、描述、分类、默认单位、建议保质期、存放位置、备注等
   - 类似于 Wiki 页面，每种物品只有一个 Wiki 条目
   - 关联 `ItemWikiCategory` 分类系统

2. **Item（库存记录）**：具体的库存实例
   - 存储具体的库存信息：数量、过期日期、购买日期等
   - 关联到 `ItemWiki`，继承 Wiki 的通用属性
   - 每个 Wiki 可以有多条库存记录（不同批次的同类物品）

### 已实现的核心功能

1. **物品 Wiki 体系**：ItemWiki + Item 双层架构
2. **库存管理**：跟踪物品的库存数量、过期日期、购买日期
3. **过期提醒**：自动计算提醒日期，支持提醒开关
4. **分类管理**：内置食品、日用品、化妆品、药品等分类
5. **标签系统**：为物品添加自定义标签
6. **中文字体支持**：自动检测并应用中文字体

### UI 页面结构

| 页面 | 说明 |
|------|------|
| `MainScreen` | 首页 - 统计概览 |
| `ItemsScreen` | 物品目录 - 左侧分类 + 右侧物品列表 |
| `ItemDetailScreen` | 库存详情页 - 单条库存记录的详细信息 |
| `ItemWikiDetailScreen` | 物品 Wiki 详情页 - 展示物品定义和所有关联库存 |
| `ItemWikiEditScreen` | 物品 Wiki 编辑页 |
| `AddItemScreen` | 添加物品表单 |
| `RecipesScreen` | 食谱页 |
| `SettingsScreen` | 设置页 |
| `AddEntryScreen` | 选择添加方式页 |

### 底部导航栏

- 首页 (home-outline)
- 物品 (fridge-outline)
- ➕ (plus)
- 食谱 (silverware-fork-knife)
- 设置 (cog-outline)

## 技术栈

### 现有技术栈

| 组件 | 技术 |
|------|------|
| **UI 框架** | Kivy + KivyMD (Material Design 3) |
| **数据库** | SQLite + SQLAlchemy ORM |
| **Python 版本** | 3.x |
| **依赖管理** | Conda (环境名: kivy) |
| **样式系统** | Material Design 3 (designed_tokens.py) |
| **字体** | 自动中文字体检测支持 |

## 项目结构

```
vibe-fridge/
├── app/
│   ├── __init__.py
│   ├── main.py                 # 应用入口和主应用类
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   ├── item.py             # Item（库存记录）模型
│   │   └── item_wiki.py        # ItemWiki 和 ItemWikiCategory 模型
│   ├── services/               # 业务服务层
│   │   ├── database.py         # 数据库服务和会话管理
│   │   ├── item_service.py     # 物品 CRUD 服务
│   │   └── wiki_service.py     # Wiki CRUD 服务
│   ├── ui/                     # UI 层
│   │   ├── screens/            # 各页面 Screen
│   │   └── theme/              # 主题和设计令牌
│   └── utils/                  # 工具函数
│       ├── logger.py           # 日志配置
│       └── font_helper.py      # 字体辅助工具
├── tests/                      # 测试代码
├── check_wiki.py               # Wiki 检查脚本
├── requirements.txt            # Python 依赖
└── AGENTS.md                   # 本文件
```

## 数据模型详解

### ItemWiki（物品 Wiki）

```python
class ItemWiki(Base):
    id: str                      # UUID
    name: str                    # 物品名称（如"鲜牛奶"）
    description: str             # 描述
    category_id: str             # 分类 ID（外键）
    default_unit: str            # 默认单位（如"盒"、"瓶"）
    suggested_expiry_days: int   # 建议保质期（天）
    storage_location: str        # 建议存放位置
    notes: str                   # 备注信息
    image_path: str              # 物品图片路径

    # 关系
    category: ItemWikiCategory   # 分类
    items: List[Item]            # 关联的库存记录
```

### ItemWikiCategory（物品分类）

```python
class ItemWikiCategory(Base):
    id: str          # UUID
    name: str        # 分类名称（如"食品"、"日用品"）
    icon: str        # 图标名称
    color: str       # 颜色（十六进制）
    sort_order: int  # 排序顺序

    items: List[ItemWiki]  # 关联的 Wiki
```

### Item（库存记录）

```python
class Item(Base):
    id: str                    # UUID
    name: str                  # 继承自 Wiki 的名称
    wiki_id: str               # 关联的 Wiki ID
    quantity: int              # 数量
    unit: str                  # 单位
    expiry_date: date          # 过期日期
    purchase_date: date        # 购买日期
    status: ItemStatus         # 状态（ACTIVE/EXPIRED/CONSUMED）
    reminder_date: date        # 提醒日期
    is_reminder_enabled: bool  # 是否启用提醒

    # 关系
    wiki: ItemWiki             # 关联的 Wiki
    tags: List[Tag]            # 标签
```

## 服务层使用

### DatabaseService (db_service)

```python
from app.services.database import db_service

# 会话上下文管理器（推荐）
with db_service.session_scope() as session:
    # 执行数据库操作
    pass

# 获取会话（需要手动关闭）
session = db_service.get_session()
try:
    # 执行操作
    pass
finally:
    session.close()
```

### ItemService (item_service)

```python
from app.services.item_service import item_service

# 创建物品（会自动创建/关联 ItemWiki）
item = item_service.create_item(
    name="鲜牛奶",
    category="食品",
    quantity=2,
    unit="盒",
    expiry_date=date(2025, 2, 5),
)

# 获取物品
item = item_service.get_item(item_id)

# 更新物品
success = item_service.update_item(item_id, quantity=3)

# 删除物品
success = item_service.delete_item(item_id)

# 获取库存列表（按类名）
items = item_service.get_inventory_by_name("鲜牛奶")

# 获取即将过期物品
expiring = item_service.get_expiring_items(days=7)
```

### WikiService (wiki_service)

```python
from app.services.wiki_service import wiki_service

# 创建 Wiki
wiki = wiki_service.create_wiki(
    name="鲜牛奶",
    description="巴氏杀菌鲜牛奶",
    default_unit="盒",
    suggested_expiry_days=7,
    storage_location="冷藏",
)

# 获取 Wiki
wiki = wiki_service.get_wiki_by_name("鲜牛奶")

# 更新 Wiki
success = wiki_service.update_wiki(wiki_id, description="新描述")

# 获取所有分类
categories = wiki_service.get_all_categories()

# 创建分类
category = wiki_service.create_category(
    name="食品",
    icon="food-apple",
    sort_order=1,
)
```

## 样式系统

### Color Palette (app/ui/theme/design_tokens.py)

```python
COLOR_PALETTE = {
    'primary': [0.25, 0.55, 0.9, 1],
    'success': [0.13, 0.77, 0.37, 1],
    'warning': [0.96, 0.35, 0.07, 1],
    'error': [0.94, 0.27, 0.27, 1],
    'surface': [1, 1, 1, 1],
    'text_primary': [0.15, 0.15, 0.15, 1],
    'text_secondary': [0.50, 0.50, 0.50, 1],
    # ...
}
```

### Design Tokens

```python
from app.ui.theme.design_tokens import COLOR_PALETTE, DESIGN_TOKENS

COLORS = COLOR_PALETTE
FONTS = DESIGN_TOKENS
```

## 中文字体支持

应用会自动检测并应用中文字体：

1. **macOS**: 优先查找 PingFang 字体
2. **Windows/Linux**: 使用系统备选字体

```python
from app.utils.font_helper import register_chinese_font, CHINESE_FONT_NAME

# 注册并获取中文字体名称
font_name = register_chinese_font()

# 应用字体到组件
label = Label(text="你好")
label.font_name = font_name
```

## 开发设置

### 环境变量

创建 `.env` 文件（不提交到版本控制）：

```env
# 应用配置
APP_NAME=vibe-fridge

# AI 配置
SILICON_FLOW_API_KEY=your_api_key_here

# 提醒配置
REMINDER_DAYS_BEFORE=3
```

### 运行应用

```bash
# 激活 Conda 环境
conda activate kivy

# 运行应用
python -m app.main
```

## 代码规范

### 导入顺序

```python
# 标准库
import os
from datetime import datetime

# 第三方库
from kivy.uix.screenmanager import Screen
from sqlalchemy.orm import Session

# 本地模块
from app.models.item import Item
from app.services.database import db_service
```

### 服务层返回值规范

- **创建方法**: 返回 `Optional[Dict]` (成功返回字典，失败返回 None)
- **更新/删除方法**: 返回 `bool` (成功返回 True，失败返回 False)
- **查询方法**: 返回列表或单个对象

### 会话管理规范

```python
# 使用 session_scope（推荐）
with db_service.session_scope() as session:
    item = session.query(Item).first()

# 手动管理会话
session = db_service.get_session()
try:
    item = session.query(Item).first()
finally:
    session.close()
```

## 待实现功能

### AI 集成

1. **硅基流动 API 集成**
   - 物品过期日期预测
   - 智能分类建议

2. **OCR 功能**
   - 拍照识别生产/过期日期
   - 订单截图文字提取

### 高级功能

1. **Android 通知系统**
   - 过期提醒推送
   - 后台服务

2. **订单导入**
   - 盒马等购物应用订单解析

## 代码审查 TODO 列表（2025-12）

### 一、数据库与服务层

1. **已修复：SQLAlchemy 标签关联的 SAWarning**
   - `ItemService._add_tags_to_item` 已使用 `object_session(item)` 判断
   - 确保会话正确管理

2. **统一数据库会话创建方式**
   - `DatabaseService` 维护单例 `engine` 和 `SessionLocal`
   - 所有会话获取统一走 `db_service.get_session()`

3. **处理 `datetime.utcnow()` 弃用警告**
   - 模型字段使用 `datetime.utcnow()`，需改用 `datetime.now(datetime.UTC)`

4. **优化统计查询的会话使用**
   - `ItemStatisticsService.get_expiry_stats` 内部多次调用服务导致多次会话开启
   - 应统一使用一个 `session_scope`

### 二、UI 修复

1. **AddItemScreen**
   - 修复成功弹窗的关闭逻辑（`success_dialog` 未正确设置）
   - 移除对不存在属性 `category_menu` 的访问
   - 修复类别按钮文字更新问题

2. **ItemDetailScreen & MainScreen**
   - 实现编辑功能
   - 统一 item_id 传递方式
   - 优化统计刷新逻辑

3. **字体应用**
   - 减少重复字体应用逻辑

### 三、测试与质量改进

1. **修复 pytest 返回非 None 的警告**
   - 移除测试函数末尾的 `return True`

2. **补充 UI 流程集成测试**
   - 添加物品表单验证测试
   - 添加删除流程测试

## Codex 特别说明

### .Codex/settings.local.json

已配置特定 Bash 命令的权限。

### 关键约定

1. **创建物品时自动创建 Wiki**
   - `ItemService.create_item` 会检查是否存在同名 Wiki
   - 不存在则创建新 Wiki

2. **Wiki 和 Item 的关系**
   - Item 必须关联到 Wiki
   - 删除 Wiki 时需检查是否有关联库存记录

3. **状态管理**
   - `ACTIVE`: 正常使用中
   - `EXPIRED`: 已过期
   - `CONSUMED`: 已消耗

4. **默认分类**
   - 应用启动时会自动创建缺失的默认分类
   - 分类包括：食品、日用品、化妆品、药品、其他
