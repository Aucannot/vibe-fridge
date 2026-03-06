from app.bot.config import BotConfig
from app.bot.engine import HybridBotEngine
from app.bot.qq_adapter import OneBotAdapter, QQMessageEvent


def test_tool_call_calc() -> None:
    engine = HybridBotEngine(config=BotConfig())
    text = engine.handle_message(user_id="u1", message="/tool calc 2+3*4")
    assert "14" in text


def test_chat_memory_hint() -> None:
    engine = HybridBotEngine(config=BotConfig(memory_turns=5))
    text = engine.handle_message(user_id="u1", message="你好")
    assert "记住你最近 1 轮消息" in text


def test_onebot_adapter_payload() -> None:
    engine = HybridBotEngine(config=BotConfig())
    adapter = OneBotAdapter(engine)
    payload = adapter.on_message_event(
        QQMessageEvent(user_id="u1", group_id="g1", message="hello")
    )
    assert payload["action"] == "send_group_msg"
    assert payload["params"]["group_id"] == "g1"
