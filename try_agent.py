import asyncio

from app.agent import run_agent
from app.llm import complete
from app.tools.base import Tool, ToolError
from app.tools.registry import ToolRegistry

PAIR = {
    "type": "object",
    "properties": {
        "a": {"type": "number", "description": "First number"},
        "b": {"type": "number", "description": "Second number"},
    },
    "required": ["a", "b"],
    "additionalProperties": False,
}


def multiply(a: float, b: float) -> float:
    return a * b


def divide(a: float, b: float) -> float:
    if b == 0:
        raise ToolError("Division by zero. Choose a non-zero divisor.")
    return a / b


registry = ToolRegistry()
registry.register(Tool("multiply", "Multiply two numbers exactly.", PAIR, multiply))
registry.register(Tool("divide", "Divide a by b exactly.", PAIR, divide))

QUESTIONS = [
    "Say hello in French.",
    "What is 17 times 23, divided by 4?",
    "What is 100 divided by 0? Explain what happened.",
]


async def main():
    for question in QUESTIONS:
        print(f"\n=== {question}")
        async for ev in run_agent(question, registry, complete):
            if ev["type"] == "tool_call":
                print(f"  -> {ev['name']}({ev['arguments']})")
            elif ev["type"] == "tool_result":
                print(f"  <- {ev['content']}  [{'ok' if ev['ok'] else 'ERROR'}, {ev['ms']} ms]")
            elif ev["type"] == "answer":
                print(f"  ANSWER{' (forced)' if ev.get('truncated') else ''}: {ev['text']}")
            elif ev["type"] == "usage":
                print(f"  tokens: in={ev['in']} out={ev['out']}")
            elif ev["type"] == "done":
                print(f"  done in {ev['steps']} step(s)")


asyncio.run(main())