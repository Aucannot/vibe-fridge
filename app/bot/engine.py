from dataclasses import dataclass, field

from .config import BotConfig
from .persona import PersonaStyler
from .tool_registry import ToolRegistry


@dataclass
class HybridBotEngine:
    """核心编排层：

    - maibot: 用 PersonaStyler 做输出润色
    - openclaw: 用 ToolRegistry 做工具调用
    """

    config: BotConfig
    persona: PersonaStyler = field(init=False)
    tools: ToolRegistry = field(default_factory=ToolRegistry)
    _memory: list[tuple[str, str]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.persona = PersonaStyler(name=self.config.persona_name)

    def handle_message(self, user_id: str, message: str) -> str:
        self._memory.append((user_id, message))
        self._memory = self._memory[-self.config.memory_turns :]

        if message.startswith(self.config.tool_call_prefix):
            result = self._handle_tool_call(message)
            return self.persona.render(f"工具结果：{result}")

        response = self._build_contextual_response(user_id=user_id, message=message)
        return self.persona.render(response)

    def _handle_tool_call(self, message: str) -> str:
        payload = message[len(self.config.tool_call_prefix) :].strip()
        if not payload:
            return "格式示例：/tool calc 12*8"

        tool_name, _, tool_payload = payload.partition(" ")
        return self.tools.execute(tool_name=tool_name, payload=tool_payload)

    def _build_contextual_response(self, user_id: str, message: str) -> str:
        history_size = len([uid for uid, _ in self._memory if uid == user_id])
        return (
            f"你刚刚说的是：{message}。"
            f"我已经记住你最近 {history_size} 轮消息。"
            "如果你要我查时间、做计算、或者回显文本，可以直接用 /tool 指令。"
        )
