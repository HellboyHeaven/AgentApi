import asyncio
import json
import sys

import httpx

from app.config import settings


async def main(query: str) -> None:
    async with httpx.AsyncClient(timeout=settings.rag_timeout_s) as client:
        resp = await client.get(f"{settings.rag_api_url}/search", params={"q": query, "k": 3})
    print("STATUS:", resp.status_code)
    data = resp.json()
    if isinstance(data, list):
        for h in data:
            print(f"{h['distance']:.3f}  {h['filename']}#{h['position']}  {h['content'][:80]!r}")
        print()
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "test"))