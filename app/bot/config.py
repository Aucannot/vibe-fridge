from dataclasses import dataclass
import os


@dataclass
class BotConfig:
    """QQ 机器人运行配置。"""

    model_name: str = "gpt-4o-mini"
    persona_name: str = "小冰箱"
    temperature: float = 0.75
    memory_turns: int = 12
    tool_call_prefix: str = "/tool"
    qq_bot_qq: str = ""

    @classmethod
    def from_env(cls) -> "BotConfig":
        return cls(
            model_name=os.getenv("HYBRID_BOT_MODEL", "gpt-4o-mini"),
            persona_name=os.getenv("HYBRID_BOT_PERSONA", "小冰箱"),
            temperature=float(os.getenv("HYBRID_BOT_TEMP", "0.75")),
            memory_turns=int(os.getenv("HYBRID_BOT_MEMORY_TURNS", "12")),
            tool_call_prefix=os.getenv("HYBRID_BOT_TOOL_PREFIX", "/tool"),
            qq_bot_qq=os.getenv("QQ_BOT_QQ", ""),
        )
