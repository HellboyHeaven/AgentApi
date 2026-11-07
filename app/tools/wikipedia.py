import httpx

from app.tools.base import Tool, ToolError

# Wikipedia просит осмысленный User-Agent, без него бывают 403
USER_AGENT = "AgentApi/0.1 (learning project; contact: you@example.com)"
MAX_RESULTS = 3
MAX_EXTRACT_CHARS = 1200
HTTP_TIMEOUT_S = 8.0  # меньше таймаута реестра, чтобы ошибка была понятной


async def search_wikipedia(
    query: str,
    lang: str = "ru",
    *,
    transport: httpx.AsyncBaseTransport | None = None,  # для тестов
) -> str:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": MAX_RESULTS,
        "prop": "extracts",
        "exintro": 1,        # только вводный абзац
        "explaintext": 1,    # без HTML
        "exlimit": "max",
        "redirects": 1,
    }
    url = f"https://{lang}.wikipedia.org/w/api.php"  # lang уже проверен enum-ом в схеме

    try:
        async with httpx.AsyncClient(
            timeout=HTTP_TIMEOUT_S,
            headers={"User-Agent": USER_AGENT},
            transport=transport,
        ) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.TimeoutException:
        raise ToolError("Wikipedia did not respond in time. Try again or answer without it.")
    except (httpx.HTTPError, ValueError):
        raise ToolError("Wikipedia is unavailable right now.")

    pages = (data.get("query") or {}).get("pages") or {}
    if not pages:
        raise ToolError(
            f"Nothing found for '{query}'. Try different keywords or another language."
        )

    items = sorted(pages.values(), key=lambda p: p.get("index", 0))
    chunks = []
    for p in items:
        extract = (p.get("extract") or "").strip()
        if not extract:
            continue
        if len(extract) > MAX_EXTRACT_CHARS:
            extract = extract[:MAX_EXTRACT_CHARS] + "…"
        chunks.append(f"## {p['title']}\n{extract}")

    if not chunks:
        raise ToolError(f"Found pages for '{query}', but they have no text.")
    return "\n\n".join(chunks)


WIKIPEDIA_SEARCH = Tool(
    name="wikipedia_search",
    description=(
        "Search Wikipedia for encyclopedic facts about people, places, events, "
        "concepts, science. Returns intro paragraphs of up to 3 best articles. "
        "Use short keyword queries (e.g. 'Эйфелева башня'), not full questions. "
        "Do NOT use for the user's own documents or for current news."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "minLength": 2, "maxLength": 200},
            "lang": {"type": "string", "enum": ["ru", "en"], "default": "ru"},
        },
        "required": ["query"],
        "additionalProperties": False,
    },
    func=search_wikipedia,
)