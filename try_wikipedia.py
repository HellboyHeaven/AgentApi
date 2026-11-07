import asyncio
import json
import sys

import httpx

USER_AGENT = "AgentApi/0.1 (learning project; contact: you@example.com)"


async def main(query: str, lang: str = "ru") -> None:
    params = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": query,
        "gsrlimit": 3,
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "exlimit": "max",
        "redirects": 1,
    }
    url = f"https://{lang}.wikipedia.org/w/api.php"

    async with httpx.AsyncClient(timeout=8, headers={"User-Agent": USER_AGENT}) as client:
        resp = await client.get(url, params=params)

    print("STATUS:", resp.status_code)
    print(json.dumps(resp.json(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "Санкт-Петербург"
    lang = sys.argv[2] if len(sys.argv) > 2 else "ru"
    asyncio.run(main(q, lang))