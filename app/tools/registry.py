import asyncio
import inspect
import json
import logging
from dataclasses import dataclass
from typing import Any

from jsonschema import Draft202012Validator

from app.config import settings
from app.tools.base import Tool, ToolError

logger = logging.getLogger(__name__)


@dataclass
class ToolResult:
    name: str
    ok: bool
    content: str  # always text: this is what goes back to the model


class ToolRegistry:
    def __init__(
        self,
        timeout_s: float | None = None,
        max_output_chars: int | None = None,
    ) -> None:
        self._tools: dict[str, Tool] = {}
        self.timeout_s = settings.tool_timeout_s if timeout_s is None else timeout_s
        self.max_output_chars = (
            settings.max_tool_output_chars if max_output_chars is None else max_output_chars
        )

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")
        self._tools[tool.name] = tool

    def schemas(self) -> list[dict]:
        return [t.schema() for t in self._tools.values()]

    async def execute(self, name: str, raw_arguments: str | None) -> ToolResult:
        """Run a tool requested by the model. Never raises: every failure becomes text."""

        def fail(message: str) -> ToolResult:
            return ToolResult(name, False, f"Error: {message}")

        tool = self._tools.get(name)
        if tool is None:
            available = ", ".join(sorted(self._tools)) or "none"
            return fail(f"unknown tool '{name}'. Available tools: {available}.")

        # 1. Arguments arrive as a JSON string and may be malformed.
        #    Some models send an empty string for tools without arguments.
        try:
            args = json.loads(raw_arguments) if raw_arguments and raw_arguments.strip() else {}
        except json.JSONDecodeError as e:
            return fail(f"the arguments are not valid JSON ({e.msg}). Send a JSON object.")
        if not isinstance(args, dict):
            return fail("the arguments must be a JSON object.")

        # 2. Validate against the schema: required fields, types, ranges
        errors = list(Draft202012Validator(tool.parameters).iter_errors(args))
        if errors:
            details = "; ".join(
                f"{'.'.join(map(str, e.path)) or 'arguments'}: {e.message}" for e in errors[:3]
            )
            return fail(f"invalid arguments for '{name}': {details}")

        # 3. Run with a timeout and turn every failure into text
        try:
            result = await asyncio.wait_for(self._call(tool, args), timeout=self.timeout_s)
        except asyncio.TimeoutError:
            return fail(f"'{name}' took longer than {self.timeout_s:g} seconds.")
        except ToolError as e:
            return fail(str(e))  # expected problem, the message was written for the model
        except Exception:
            # Unexpected bug: keep the details in the log, not in the model's context
            logger.exception("Tool '%s' crashed", name)
            return fail(f"'{name}' failed unexpectedly.")

        return ToolResult(name, True, self._to_text(result))

    @staticmethod
    async def _call(tool: Tool, args: dict[str, Any]) -> Any:
        if inspect.iscoroutinefunction(tool.func):
            return await tool.func(**args)
        # Sync tools run in a worker thread so they cannot block the event loop
        return await asyncio.to_thread(tool.func, **args)

    def _to_text(self, result: Any) -> str:
        text = result if isinstance(result, str) else json.dumps(
            result, ensure_ascii=False, default=str
        )
        if len(text) > self.max_output_chars:
            text = text[: self.max_output_chars] + "\n[output truncated]"
        return text