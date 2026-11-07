from app.tools.calculator import CALCULATOR
from app.tools.clock import CURRENT_TIME
from app.tools.documents import SEARCH_DOCUMENTS
from app.tools.registry import ToolRegistry
from app.tools.wikipedia import WIKIPEDIA_SEARCH


def build_registry() -> ToolRegistry:
    """The registry with all built-in tools. More tools will be added here."""
    registry = ToolRegistry()
    for tool in (CALCULATOR, CURRENT_TIME, WIKIPEDIA_SEARCH, SEARCH_DOCUMENTS):
        registry.register(tool)
    return registry