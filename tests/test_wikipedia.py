import httpx, pytest
from app.tools.wikipedia import search_wikipedia
from app.tools.base import ToolError

def make_transport(payload, status=200):
    return httpx.MockTransport(lambda req: httpx.Response(status, json=payload))

async def test_returns_articles():
    payload = {"query": {"pages": {"1": {"title": "Париж", "index": 1, "extract": "Столица Франции."}}}}
    out = await search_wikipedia("Париж", transport=make_transport(payload))
    assert "## Париж" in out

async def test_nothing_found():
    with pytest.raises(ToolError):
        await search_wikipedia("zzzzqq", transport=make_transport({"batchcomplete": ""}))

async def test_http_error():
    with pytest.raises(ToolError):
        await search_wikipedia("x", transport=make_transport({}, status=500))