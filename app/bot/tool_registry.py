import ast
from collections.abc import Callable
from datetime import datetime


ToolHandler = Callable[[str], str]


class ToolRegistry:
    """模拟 openclaw 风格的工具路由。"""

    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {
            "time": self._time_tool,
            "calc": self._calc_tool,
            "echo": self._echo_tool,
        }

    def available_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def execute(self, tool_name: str, payload: str) -> str:
        tool = self._tools.get(tool_name)
        if tool is None:
            return f"未知工具: {tool_name}，可用工具: {', '.join(self.available_tools())}"
        return tool(payload)

    def _time_tool(self, _: str) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _calc_tool(self, expression: str) -> str:
        node = ast.parse(expression, mode="eval")
        if not self._is_safe_math(node):
            return "仅支持四则运算表达式"
        return str(eval(compile(node, "<calc>", "eval"), {"__builtins__": {}}, {}))

    def _echo_tool(self, payload: str) -> str:
        return payload

    def _is_safe_math(self, node: ast.AST) -> bool:
        allowed_nodes = (
            ast.Expression,
            ast.BinOp,
            ast.UnaryOp,
            ast.Constant,
            ast.Add,
            ast.Sub,
            ast.Mult,
            ast.Div,
            ast.Mod,
            ast.Pow,
            ast.USub,
            ast.UAdd,
            ast.Load,
            ast.FloorDiv,
            ast.Call,
            ast.Name,
        )

        for sub_node in ast.walk(node):
            if not isinstance(sub_node, allowed_nodes):
                return False
            if isinstance(sub_node, ast.Call):
                return False
            if isinstance(sub_node, ast.Name):
                return False
        return True
