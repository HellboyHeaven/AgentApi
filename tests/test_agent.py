from types import SimpleNamespace

import pytest

from app.agent import DUPLICATE_CALL, FORCE_ANSWER, run_agent
from app.tools.base import Tool
from app.tools.registry import ToolRegistry

SCHEMA = {
    "type": "object",
    "properties": {"n": {"type": "integer"}},
    "required": ["n"],
    "additionalProperties": False,
}


def response(content=None, calls=(), tokens=(10, 5)):
    """Builds a fake chat completion. calls: [(call_id, tool_name, raw_arguments)]."""
    tool_calls = [
        SimpleNamespace(id=cid, function=SimpleNamespace(name=name, arguments=args))
        for cid, name, args in calls
    ] or None
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content, tool_calls=tool_calls))],
        usage=SimpleNamespace(prompt_tokens=tokens[0], completion_tokens=tokens[1]),
    )


class ScriptedModel:
    """Returns prepared responses in order and records every call it receives."""

    def __init__(self, *responses):
        self._responses = list(responses)
        self.calls = []

    async def __call__(self, messages, tools):
        self.calls.append({"messages": list(messages), "tools": tools})
        return self._responses.pop(0)


@pytest.fixture
def runs():
    return []


@pytest.fixture
def registry(runs):
    def double(n):
        runs.append(n)
        return n * 2

    r = ToolRegistry(timeout_s=1)
    r.register(Tool("double", "Double a number.", SCHEMA, double))
    return r


async def collect(question, registry, model, max_steps=4):
    return [e async for e in run_agent(question, registry, model, max_steps=max_steps)]


def types(events):
    return [e["type"] for e in events]


async def test_direct_answer_without_tools(registry, runs):
    model = ScriptedModel(response("Hello!"))

    events = await collect("hi", registry, model)

    assert types(events) == ["answer", "usage", "done"]
    assert events[0]["text"] == "Hello!"
    assert events[-1]["steps"] == 1
    assert runs == [] and len(model.calls) == 1


async def test_tool_call_then_answer(registry, runs):
    model = ScriptedModel(
        response(calls=[("c1", "double", '{"n": 21}')]),
        response("The result is 42."),
    )

    events = await collect("double 21", registry, model)

    assert types(events) == ["tool_call", "tool_result", "answer", "usage", "done"]
    assert events[1]["ok"] and events[1]["content"] == "42"
    assert events[2]["text"] == "The result is 42."
    assert runs == [21]


async def test_tool_result_is_sent_back_linked_by_id(registry):
    model = ScriptedModel(
        response(calls=[("c1", "double", '{"n": 1}')]),
        response("done"),
    )

    await collect("q", registry, model)

    second_call = model.calls[1]["messages"]
    assert second_call[-2]["role"] == "assistant"
    assert second_call[-2]["tool_calls"][0]["id"] == "c1"
    assert second_call[-1] == {"role": "tool", "tool_call_id": "c1", "content": "2"}


async def test_parallel_calls_each_get_a_result(registry, runs):
    model = ScriptedModel(
        response(calls=[("c1", "double", '{"n": 1}'), ("c2", "double", '{"n": 2}')]),
        response("done"),
    )

    events = await collect("q", registry, model)

    results = [e for e in events if e["type"] == "tool_result"]
    assert [(r["id"], r["content"]) for r in results] == [("c1", "2"), ("c2", "4")]
    tool_messages = [m for m in model.calls[1]["messages"] if m["role"] == "tool"]
    assert [m["tool_call_id"] for m in tool_messages] == ["c1", "c2"]


async def test_unknown_tool_error_goes_back_to_the_model(registry):
    model = ScriptedModel(
        response(calls=[("c1", "nope", "{}")]),
        response("Sorry, I used the wrong tool."),
    )

    events = await collect("q", registry, model)

    result = next(e for e in events if e["type"] == "tool_result")
    assert not result["ok"] and "unknown tool 'nope'" in result["content"]
    assert events[-3]["text"] == "Sorry, I used the wrong tool."  # the run was not aborted


async def test_model_can_recover_from_invalid_arguments(registry, runs):
    model = ScriptedModel(
        response(calls=[("c1", "double", '{"n": "five"}')]),  # wrong type
        response(calls=[("c2", "double", '{"n": 5}')]),       # corrected
        response("10"),
    )

    events = await collect("double five", registry, model)

    results = [e for e in events if e["type"] == "tool_result"]
    assert [r["ok"] for r in results] == [False, True]
    assert runs == [5]


async def test_duplicate_call_is_not_executed_twice(registry, runs):
    model = ScriptedModel(
        response(calls=[("c1", "double", '{"n": 7}')]),
        response(calls=[("c2", "double", '{"n": 7}')]),  # exactly the same call
        response("14"),
    )

    events = await collect("q", registry, model)

    results = [e for e in events if e["type"] == "tool_result"]
    assert results[0]["ok"]
    assert not results[1]["ok"] and results[1]["content"] == DUPLICATE_CALL.format(name="double")
    assert runs == [7]  # the tool ran only once


async def test_argument_order_does_not_hide_a_duplicate():
    r = ToolRegistry(timeout_s=1)
    runs = []
    pair = {
        "type": "object",
        "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
        "required": ["a", "b"],
    }
    r.register(Tool("add", "Add.", pair, lambda a, b: runs.append((a, b)) or a + b))
    model = ScriptedModel(
        response(calls=[("c1", "add", '{"a": 1, "b": 2}')]),
        response(calls=[("c2", "add", '{"b": 2, "a": 1}')]),  # same call, different key order
        response("3"),
    )

    await collect("q", r, model)

    assert len(runs) == 1


async def test_step_limit_forces_a_final_answer(registry, runs):
    model = ScriptedModel(
        response(calls=[("c1", "double", '{"n": 1}')]),
        response(calls=[("c2", "double", '{"n": 2}')]),
        response("Best effort answer."),  # the forced call
    )

    events = await collect("q", registry, model, max_steps=2)

    answer = next(e for e in events if e["type"] == "answer")
    assert answer["text"] == "Best effort answer." and answer["truncated"] is True
    assert events[-1] == {"type": "done", "steps": 2}
    assert runs == [1, 2]
    # The last call is made WITHOUT tools and carries the instruction to answer now
    assert model.calls[-1]["tools"] is None
    assert model.calls[-1]["messages"][-1] == {"role": "user", "content": FORCE_ANSWER}
    # Normal calls did offer the tools
    assert model.calls[0]["tools"]


async def test_usage_is_summed_over_all_model_calls(registry):
    model = ScriptedModel(
        response(calls=[("c1", "double", '{"n": 1}')], tokens=(100, 10)),
        response("done", tokens=(150, 20)),
    )

    events = await collect("q", registry, model)

    usage = next(e for e in events if e["type"] == "usage")
    assert (usage["in"], usage["out"]) == (250, 30)


async def test_missing_usage_does_not_break_the_run(registry):
    bare = response("ok")
    bare.usage = None
    events = await collect("q", registry, ScriptedModel(bare))
    assert next(e for e in events if e["type"] == "usage") == {"type": "usage", "in": 0, "out": 0}


async def test_model_errors_propagate_to_the_caller(registry):
    async def broken(messages, tools):
        raise RuntimeError("model is down")

    with pytest.raises(RuntimeError):
        await collect("q", registry, broken)