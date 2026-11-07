from dataclasses import dataclass
from typing import Any, Callable


class ToolError(Exception):
    """Raised by a tool for an expected problem (bad input, nothing found, ...).

    The message is sent to the model, so it must be safe to show and tell
    the model what to do differently.
    """


@dataclass(frozen=True)
class Tool:
    name: str
    description: str          # this is effectively a prompt: the model picks tools by it
    parameters: dict[str, Any]  # JSON Schema of the arguments
    func: Callable[..., Any]    # sync or async function

    def schema(self) -> dict:
        """The description sent to the model."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }