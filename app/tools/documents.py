import httpx

from app.config import settings
from app.tools.base import Tool, ToolError

MAX_RESULTS = 4
MAX_CHUNK_CHARS = 800


async def search_documents(
    query: str,
    *,
    transport: httpx.AsyncBaseTransport | None = None,  # для тестов
) -> str:
    # URL берётся только из конфига: модель управляет лишь текстом запроса
    url = f"{settings.rag_api_url.rstrip('/')}/search"
    try:
        async with httpx.AsyncClient(timeout=settings.rag_timeout_s, transport=transport) as client:
            resp = await client.get(url, params={"q": query, "k": MAX_RESULTS})
            resp.raise_for_status()
            hits = resp.json()
    except httpx.TimeoutException:
        raise ToolError("The document search did not respond in time. Try again.")
    except (httpx.HTTPError, ValueError):
        raise ToolError("The document search is unavailable right now.")

    if not isinstance(hits, list):
        raise ToolError("The document search returned an unexpected response.")

    chunks = []
    for i, h in enumerate(hits[:MAX_RESULTS], start=1):
        content = (h.get("content") or "").strip()
        if not content:
            continue
        if len(content) > MAX_CHUNK_CHARS:
            content = content[:MAX_CHUNK_CHARS] + "…"
        source = f"{h.get('filename', 'unknown')} (part {h.get('position', '?')})"
        chunks.append(f"[{i}] source: {source}\n{content}")

    if not chunks:
        raise ToolError(f"No relevant documents found for '{query}'. Try different keywords.")
    return "\n\n".join(chunks)


SEARCH_DOCUMENTS = Tool(
    name="search_documents",
    description=(
        "Search the user's own uploaded documents (the private knowledge base). "
        "Returns the most relevant text fragments with their file names. "
        "Use for any question about the user's files, notes or internal materials. "
        "Do NOT use for general encyclopedic facts: that is wikipedia_search."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "minLength": 2, "maxLength": 300},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    func=search_documents,
)