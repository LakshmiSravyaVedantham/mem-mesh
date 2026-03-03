from __future__ import annotations

import asyncio

import httpx
from fastapi import FastAPI, Request, Response

from mem_mesh.extractor import MemoryExtractor
from mem_mesh.injector import MemoryInjector
from mem_mesh.store import MemoryStore

_DEFAULT_TARGET = "https://api.anthropic.com"
_TIMEOUT = 120.0
_HOP_BY_HOP = frozenset({"host", "content-length", "transfer-encoding", "connection"})


def build_app(
    store: MemoryStore | None = None,
    target_url: str = _DEFAULT_TARGET,
) -> FastAPI:
    _store = store or MemoryStore()
    injector = MemoryInjector(_store)
    extractor = MemoryExtractor()

    app = FastAPI(title="mem-mesh proxy")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/v1/messages")
    async def proxy_messages(request: Request) -> Response:
        body: dict = await request.json()  # type: ignore[type-arg]
        modified = injector.inject(body)

        forward_headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in _HOP_BY_HOP
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{target_url}/v1/messages",
                json=modified,
                headers=forward_headers,
                timeout=_TIMEOUT,
            )

        # Fire-and-forget memory extraction (never crashes the proxy)
        messages: list[dict] = body.get("messages", [])  # type: ignore[type-arg]
        asyncio.create_task(
            _extract_and_store(extractor, _store, messages, resp.json())
        )

        return Response(
            content=resp.content,
            status_code=resp.status_code,
            media_type="application/json",
        )

    return app


async def _extract_and_store(
    extractor: MemoryExtractor,
    store: MemoryStore,
    messages: list[dict],  # type: ignore[type-arg]
    response_body: dict,  # type: ignore[type-arg]
) -> None:
    try:
        content = response_body.get("content", [])
        assistant_text = " ".join(
            c.get("text", "") for c in content if isinstance(c, dict)
        )
        all_messages = messages + [{"role": "assistant", "content": assistant_text}]
        entries = extractor.extract(all_messages)
        for entry in entries:
            store.write(entry)
    except Exception:
        pass  # Never crash the proxy due to extraction failure
