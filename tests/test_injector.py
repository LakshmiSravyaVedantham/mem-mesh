import pytest
from pathlib import Path
from mem_mesh.injector import MemoryInjector
from mem_mesh.store import MemoryStore, MemoryEntry


def _make_store_with_entries(tmp_path: Path) -> MemoryStore:
    store = MemoryStore(tmp_path / "mem-mesh")
    store.write(MemoryEntry("Prefers Python", "preferences", "claude", "2026-03-03T10:00:00"))
    store.write(MemoryEntry("Lives in San Jose", "facts", "claude", "2026-03-03T10:01:00"))
    return store


def test_inject_adds_system_when_absent(tmp_path: Path) -> None:
    store = _make_store_with_entries(tmp_path)
    injector = MemoryInjector(store)
    body = {"model": "claude-sonnet-4-6", "messages": [{"role": "user", "content": "hi"}]}
    result = injector.inject(body)
    assert "system" in result
    assert "Prefers Python" in result["system"]


def test_inject_prepends_to_existing_system(tmp_path: Path) -> None:
    store = _make_store_with_entries(tmp_path)
    injector = MemoryInjector(store)
    body = {
        "model": "claude-sonnet-4-6",
        "system": "You are a helpful assistant.",
        "messages": [],
    }
    result = injector.inject(body)
    assert result["system"].startswith("[MEMORY CONTEXT]")
    assert "You are a helpful assistant." in result["system"]


def test_inject_does_not_modify_original_body(tmp_path: Path) -> None:
    store = _make_store_with_entries(tmp_path)
    injector = MemoryInjector(store)
    body = {"system": "Original system", "messages": []}
    original_system = body["system"]
    injector.inject(body)
    assert body["system"] == original_system


def test_inject_returns_unchanged_when_no_memories(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "empty-store")
    injector = MemoryInjector(store)
    body = {"system": "Original", "messages": []}
    result = injector.inject(body)
    assert result["system"] == "Original"


def test_inject_limits_to_top_5_memories(tmp_path: Path) -> None:
    store = MemoryStore(tmp_path / "mem-mesh")
    for i in range(10):
        store.write(MemoryEntry(f"Memory {i}", "preferences", "claude", f"2026-03-03T10:0{i}:00"))
    injector = MemoryInjector(store)
    result = injector.inject({"messages": []})
    memory_block = result["system"].split("[/MEMORY CONTEXT]")[0]
    lines = [l for l in memory_block.splitlines() if l.startswith("- ")]
    assert len(lines) <= 5
