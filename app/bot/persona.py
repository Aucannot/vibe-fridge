from dataclasses import dataclass
from random import choice


@dataclass
class PersonaStyler:
    """模拟 maibot 风格：口语化、情绪化、短句分段。"""

    name: str = "小冰箱"

    _openers = (
        "我在～",
        "来啦来啦，",
        "我想了下，",
        "这个我会！",
    )
    _enders = (
        "要不要我再细化下一步？",
        "你点头我就开干。",
        "我可以直接帮你生成配置。",
        "如果你愿意，我还能顺便做成可部署版本。",
    )

    def render(self, plain_response: str) -> str:
        opener = choice(self._openers)
        ender = choice(self._enders)
        content = plain_response.strip()
        if not content:
            content = "我在听，你继续说。"
        return f"{opener}\n{content}\n{ender}"
