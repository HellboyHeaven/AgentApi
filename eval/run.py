import asyncio

from app.agent import run_agent
from app.llm import complete
from app.tools.builtin import build_registry
from eval.questions import QUESTIONS




async def run_one(case) -> tuple[bool, set[str]]:
    registry = build_registry()
    called: set[str] = set()
    async for ev in run_agent(case["q"], registry, complete):
        if ev["type"] == "tool_call":
            called.add(ev["name"])
    ok = case["required"] <= called and not (case["forbidden"] & called)
    return ok, called


async def main() -> None:
    passed = 0
    for case in QUESTIONS:
        ok, called = await run_one(case)
        passed += ok
        mark = "PASS" if ok else "FAIL"
        print(f"{mark}  {case['q'][:55]:55}  called={sorted(called)}")
        await asyncio.sleep(1)
    print(f"\n{passed}/{len(QUESTIONS)} passed")


if __name__ == "__main__":
    asyncio.run(main())