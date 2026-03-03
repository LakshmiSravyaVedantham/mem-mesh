from __future__ import annotations

from mem_mesh.store import MemoryStore

MEMORY_BLOCK_TEMPLATE = "[MEMORY CONTEXT]\n{memories}\n[/MEMORY CONTEXT]\n\n"


class MemoryInjector:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def inject(self, request_body: dict) -> dict:  # type: ignore[type-arg]
        memories = self.store.read_all()
        if not memories:
            return request_body

        top = sorted(memories, key=lambda e: e.timestamp, reverse=True)[:5]
        memory_lines = "\n".join(f"- {e.content}" for e in top)
        memory_block = MEMORY_BLOCK_TEMPLATE.format(memories=memory_lines)

        body = dict(request_body)
        existing = body.get("system", "")
        body["system"] = memory_block + existing
        return body
