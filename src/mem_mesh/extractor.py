from __future__ import annotations

import json
from datetime import datetime, timezone

import anthropic
from anthropic.types import TextBlock

from mem_mesh.store import MemoryEntry

VALID_CATEGORIES = frozenset({"preferences", "facts", "corrections"})

EXTRACTION_PROMPT = """Extract memory signals from this AI conversation. Return a JSON array only — no prose.

Each item must be: {{"content": "specific memory", "category": "preferences|facts|corrections"}}

Rules:
- preferences: user style, workflow, or tool preferences
- facts: facts the user stated about themselves
- corrections: things the user explicitly corrected the AI on
- Return [] if nothing is worth remembering
- Maximum 5 items
- Be specific, not vague

Conversation:
{conversation}

JSON array:"""


class MemoryExtractor:
    def __init__(self, client: anthropic.Anthropic | None = None) -> None:
        self.client = client or anthropic.Anthropic()

    def extract(
        self, messages: list[dict[str, str]], source_tool: str = "unknown"
    ) -> list[MemoryEntry]:
        """Extract memory signals from a conversation using Claude Haiku.

        Only the last 10 messages are sent to the extraction model to
        keep token usage bounded. Returns [] if no signals found or on any error.
        """
        if not messages:
            return []

        conversation = "\n".join(
            f"{m['role'].upper()}: {m.get('content', '')}"
            for m in messages[-10:]
        )

        response = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(conversation=conversation),
                }
            ],
        )

        try:
            block = response.content[0]
            if not isinstance(block, TextBlock):
                return []
            text = block.text.strip()
            items: list[dict[str, str]] = json.loads(text)
            now = datetime.now(tz=timezone.utc).isoformat()
            return [
                MemoryEntry(
                    content=item.get("content", ""),
                    category=item.get("category", ""),
                    source_tool=source_tool,
                    timestamp=now,
                )
                for item in items
                if item.get("content") and item.get("category") in VALID_CATEGORIES
            ]
        except (IndexError, json.JSONDecodeError, TypeError):
            return []
