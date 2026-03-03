import json
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from mem_mesh.proxy import build_app
from mem_mesh.store import MemoryStore


@pytest.fixture
def empty_store(tmp_path: Path) -> MemoryStore:
    return MemoryStore(tmp_path / "mem-mesh")


@pytest.fixture
def app(empty_store: MemoryStore):
    return build_app(store=empty_store, target_url="http://fake-anthropic.test")


@pytest.mark.asyncio
async def test_health_endpoint(app) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_proxy_forwards_messages_request(app) -> None:
    fake_response = {
        "id": "msg_123",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "Hello"}],
    }
    with patch("mem_mesh.proxy.httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = json.dumps(fake_response).encode()
        mock_resp.headers = {"content-type": "application/json"}
        mock_resp.json.return_value = fake_response
        mock_instance.post = AsyncMock(return_value=mock_resp)
        MockClient.return_value = mock_instance

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/v1/messages",
                json={
                    "model": "claude-sonnet-4-6",
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": "hi"}],
                },
                headers={"x-api-key": "test-key", "anthropic-version": "2023-06-01"},
            )

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_proxy_injects_memories_when_present(app, empty_store: MemoryStore) -> None:
    from mem_mesh.store import MemoryEntry
    empty_store.write(MemoryEntry("Prefers Python", "preferences", "test", "2026-03-03T10:00:00"))

    captured_body: dict = {}

    with patch("mem_mesh.proxy.httpx.AsyncClient") as MockClient:
        mock_instance = AsyncMock()
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)

        async def capture_post(url, **kwargs):
            captured_body.update(kwargs.get("json", {}))
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.content = b'{"type":"message","content":[]}'
            mock_resp.headers = {}
            mock_resp.json.return_value = {"type": "message", "content": []}
            return mock_resp

        mock_instance.post = capture_post
        MockClient.return_value = mock_instance

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.post(
                "/v1/messages",
                json={"model": "claude-sonnet-4-6", "max_tokens": 10, "messages": [{"role": "user", "content": "hi"}]},
                headers={"x-api-key": "test-key", "anthropic-version": "2023-06-01"},
            )

    assert "system" in captured_body
    assert "Prefers Python" in captured_body["system"]
