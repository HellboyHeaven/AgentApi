import httpx, pytest
from app.tools.base import ToolError
from app.tools.documents import search_documents


def transport(payload, status=200):
    return httpx.MockTransport(lambda req: httpx.Response(status, json=payload))


HIT = {
    "chunk_id": 1,
    "document_id": "7f0c1c1e-0000-0000-0000-000000000000",
    "filename": "hr.pdf",
    "position": 2,
    "content": "Отпуск 28 дней.",
    "distance": 0.21,
}


async def test_returns_fragments():
    out = await search_documents("отпуск", transport=transport([HIT]))
    assert "hr.pdf (part 2)" in out and "28 дней" in out


async def test_sends_k_param():
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen.update(req.url.params)
        return httpx.Response(200, json=[HIT])

    await search_documents("отпуск", transport=httpx.MockTransport(handler))
    assert seen["q"] == "отпуск" and seen["k"] == "4"


async def test_empty_results():
    with pytest.raises(ToolError):
        await search_documents("ничего", transport=transport([]))


async def test_server_error():
    with pytest.raises(ToolError):
        await search_documents("x", transport=transport({}, status=500))