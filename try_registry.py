import asyncio

from app.tools.base import Tool, ToolError
from app.tools.registry import ToolRegistry


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ToolError("Division by zero. Choose a non-zero divisor.")
    return a / b


async def slow() -> str:
    await asyncio.sleep(5)
    return "done"


def buggy() -> str:
    return {}["missing"]  # an unexpected KeyError


NUMBER_PAIR = {
    "type": "object",
    "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
    "required": ["a", "b"],
    "additionalProperties": False,
}

registry = ToolRegistry(timeout_s=1, max_output_chars=50)
registry.register(Tool("divide", "Divide a by b.", NUMBER_PAIR, divide))
registry.register(Tool("slow", "A slow tool.", {"type": "object", "properties": {}}, slow))
registry.register(Tool("buggy", "A tool with a bug.", {"type": "object", "properties": {}}, buggy))
registry.register(Tool("long", "Returns a long text.", {"type": "object", "properties": {}}, lambda: "x" * 500))


async def main():
    cases = [
        ("works",              "divide", '{"a": 10, "b": 4}'),
        ("unknown tool",       "divid",  '{"a": 1, "b": 2}'),
        ("broken JSON",        "divide", '{"a": 1, "b": '),
        ("not an object",      "divide", "[1, 2]"),
        ("missing argument",   "divide", '{"a": 1}'),
        ("wrong type",         "divide", '{"a": "ten", "b": 2}'),
        ("extra argument",     "divide", '{"a": 1, "b": 2, "c": 3}'),
        ("tool-level error",   "divide", '{"a": 1, "b": 0}'),
        ("timeout",            "slow",   ""),
        ("unexpected crash",   "buggy",  "{}"),
        ("truncated output",   "long",   "{}"),
    ]
    for label, name, raw in cases:
        r = await registry.execute(name, raw)
        print(f"{label:<18} ok={str(r.ok):<5} {r.content!r}")


asyncio.run(main())