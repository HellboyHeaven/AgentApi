from app.tools.calculator import CALCULATOR
from app.tools.clock import CURRENT_TIME
from app.tools.registry import ToolRegistry


def build_registry() -> ToolRegistry:
    """The registry with all built-in tools. More tools will be added here."""
    registry = ToolRegistry()
    for tool in (CALCULATOR, CURRENT_TIME):
        registry.register(tool)
    return registry