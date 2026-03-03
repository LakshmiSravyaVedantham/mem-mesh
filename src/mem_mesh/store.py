from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


CATEGORIES = ("preferences", "facts", "corrections")


@dataclass
class MemoryEntry:
    content: str
    category: str
    source_tool: str
    timestamp: str


class MemoryStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path.home() / ".mem-mesh"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._init_files()

    def _init_files(self) -> None:
        for category in CATEGORIES:
            path = self.base_dir / f"{category}.md"
            if not path.exists():
                path.write_text(f"# {category.title()}\n\n")

    def write(self, entry: MemoryEntry) -> None:
        path = self.base_dir / f"{entry.category}.md"
        with path.open("a") as f:
            f.write(
                f"- [{entry.timestamp}] ({entry.source_tool}) {entry.content}\n"
            )

    def read(self, category: str) -> list[MemoryEntry]:
        path = self.base_dir / f"{category}.md"
        if not path.exists():
            return []
        entries = []
        for line in path.read_text().splitlines():
            if not line.startswith("- ["):
                continue
            try:
                ts = line[3 : line.index("]")]
                rest = line[line.index("]") + 2 :]
                tool = rest[1 : rest.index(")")]
                content = rest[rest.index(")") + 2 :]
                entries.append(
                    MemoryEntry(
                        content=content,
                        category=category,
                        source_tool=tool,
                        timestamp=ts,
                    )
                )
            except (ValueError, IndexError):
                continue
        return entries

    def read_all(self) -> list[MemoryEntry]:
        result: list[MemoryEntry] = []
        for category in CATEGORIES:
            result.extend(self.read(category))
        return result

    def search(self, query: str) -> list[MemoryEntry]:
        q = query.lower()
        return [e for e in self.read_all() if q in e.content.lower()]

    def forget(self, pattern: str) -> int:
        removed = 0
        pat = pattern.lower()
        for category in CATEGORIES:
            path = self.base_dir / f"{category}.md"
            if not path.exists():
                continue
            lines = path.read_text().splitlines(keepends=True)
            new_lines = []
            for line in lines:
                if line.startswith("- ["):
                    # Parse content field only — match against content, not timestamp/tool
                    try:
                        rest = line[line.index("]") + 2 :]
                        content = rest[rest.index(")") + 2 :].strip()
                        if pat in content.lower():
                            removed += 1
                            continue
                    except (ValueError, IndexError):
                        pass
                new_lines.append(line)
            path.write_text("".join(new_lines))
        return removed
