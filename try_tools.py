import asyncio
import json

from openai import AsyncOpenAI

from app.config import settings

client = AsyncOpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "multiply",
            "description": "Multiply two numbers exactly. Use it for any multiplication.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First factor"},
                    "b": {"type": "number", "description": "Second factor"},
                },
                "required": ["a", "b"],
            },
        },
    }
]


def multiply(a: float, b: float) -> float:
    return a * b


async def main():
    messages = [
        {"role": "user", "content": "What is 17 times 23, and what is 12 times 12?"}
    ]

    # The agent loop: ask the model, run the tools it requests, repeat until it answers.
    # The step limit protects against a model that keeps calling tools forever.
    for step in range(1, settings.max_agent_steps + 1):
        response = await client.chat.completions.create(
            model=settings.llm_model, messages=messages, tools=TOOLS
        )
        choice = response.choices[0]
        msg = choice.message
        print(f"\n--- step {step}: finish_reason={choice.finish_reason}, "
              f"tool_calls={len(msg.tool_calls or [])} ---")

        if not msg.tool_calls:
            print("FINAL ANSWER:", msg.content)
            return

        # Keep the assistant message that requested the calls in the history
        messages.append({
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)
            result = multiply(**args)
            print(f"  {tc.function.name}({args}) = {result}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": str(result),
            })

    print(f"\nStopped: no final answer after {settings.max_agent_steps} steps")


asyncio.run(main())