"""本地命令行 demo：模拟 QQ 收消息后转为 OneBot 回复。"""

from app.bot.config import BotConfig
from app.bot.engine import HybridBotEngine
from app.bot.qq_adapter import OneBotAdapter, QQMessageEvent


def main() -> None:
    engine = HybridBotEngine(config=BotConfig.from_env())
    adapter = OneBotAdapter(engine=engine)

    print("Hybrid QQ Bot demo 已启动，输入 q 退出")
    while True:
        text = input("你: ").strip()
        if text.lower() == "q":
            break

        event = QQMessageEvent(user_id="demo-user", group_id="123456", message=text)
        reply = adapter.on_message_event(event)
        print(f"bot payload: {reply}")


if __name__ == "__main__":
    main()
