from app.tools.builtin import build_registry


async def test_calculator_through_the_registry():
    r = await build_registry().execute("calculator", '{"expression": "17 * 23 / 4"}')
    assert (r.ok, r.content) == (True, "97.75")


async def test_wrong_argument_type_is_rejected_by_the_schema():
    r = await build_registry().execute("calculator", '{"expression": 5}')
    assert not r.ok


async def test_tool_error_text_reaches_the_model():
    r = await build_registry().execute("calculator", '{"expression": "1 / 0"}')
    assert not r.ok and "Division by zero" in r.content


async def test_current_time_works_without_arguments():
    for raw in ("", "{}", None):
        r = await build_registry().execute("current_time", raw)
        assert r.ok and '"timezone": "UTC"' in r.content


def test_every_tool_has_a_description_and_a_unique_name():
    schemas = [s["function"] for s in build_registry().schemas()]
    names = [s["name"] for s in schemas]
    assert len(names) == len(set(names))
    assert all(len(s["description"]) > 30 for s in schemas)