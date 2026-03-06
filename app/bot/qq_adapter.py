from dataclasses import dataclass

from .engine import HybridBotEngine


@dataclass
class QQMessageEvent:
    user_id: str
    group_id: str | None
    message: str


class OneBotAdapter:
    """适配 OneBot 风格事件。"""

    def __init__(self, engine: HybridBotEngine) -> None:
        self.engine = engine

    def on_message_event(self, event: QQMessageEvent) -> dict:
        reply = self.engine.handle_message(user_id=event.user_id, message=event.message)
        return {
            "action": "send_group_msg" if event.group_id else "send_private_msg",
            "params": {
                "group_id": event.group_id,
                "user_id": event.user_id,
                "message": reply,
            },
        }
