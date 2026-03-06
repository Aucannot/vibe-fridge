# QQ 混合机器人实现方案（maibot + openclaw）

你提到的目标是：

- **像 maibot 一样有人味**（口语化、情绪化、记忆感）
- **像 openclaw 一样全能**（工具调用、任务编排、可扩展）

本仓库已经提供了一个可运行的 MVP，在 `app/bot/` 下：

- `config.py`：环境配置读取
- `persona.py`：拟人风格渲染（maibot 风格层）
- `tool_registry.py`：工具注册与执行（openclaw 能力层）
- `engine.py`：消息编排核心
- `qq_adapter.py`：OneBot 消息适配
- `scripts/run_qq_bot_demo.py`：本地命令行模拟

## 快速运行

```bash
python scripts/run_qq_bot_demo.py
```

试试：

- 普通对话：`今天吃什么`
- 工具调用：`/tool time`
- 工具调用：`/tool calc 12*(5+3)`

## 下一步接入 QQ 平台

建议接入链路：

1. **QQ 协议端**：NapCat/LLOneBot（统一 OneBot 事件）
2. **网关服务**：FastAPI（接收 OneBot webhook）
3. **本项目引擎**：`HybridBotEngine`
4. **LLM 服务**：OpenAI 或兼容 API
5. **工具层**：把 `ToolRegistry` 扩展为搜索、日程、知识库、自动化执行

## 可扩展建议

1. 记忆层接 Redis/SQLite（区分短期/长期记忆）
2. 工具层加权限系统（群聊白名单、危险动作确认）
3. 输出层增加人格参数（撒娇度、严谨度、简洁度）
4. 增加工作流引擎（多步骤任务自动拆解和追踪）

