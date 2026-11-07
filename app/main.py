import json
import logging

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from app.agent import run_agent  # поправьте путь к вашему модулю
from app.config import settings
from app.tools.builtin import build_registry

logger = logging.getLogger(__name__)

app = FastAPI(title="AgentApi")
registry = build_registry()
llm = AsyncOpenAI(base_url=settings.llm_base_url, api_key=settings.llm_api_key)


async def complete(messages: list[dict], tools: list[dict] | None):
    kwargs = {"model": settings.llm_model, "messages": messages}
    if tools:  # tools=None отправился бы как null, поэтому передаём только когда есть
        kwargs["tools"] = tools
    return await llm.chat.completions.create(**kwargs)


class AgentRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@app.post("/agent")
async def agent(req: AgentRequest):
    async def events():
        try:
            async for event in run_agent(req.question, registry, complete):
                yield sse(event)
        except Exception:
            logger.exception("Agent crashed")
            yield sse({"type": "error", "message": "Internal error."})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}