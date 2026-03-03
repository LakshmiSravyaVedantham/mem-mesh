from pathlib import Path

from mem_mesh.store import MemoryEntry, MemoryStore


def test_store_creates_directory(tmp_store_dir: Path) -> None:
    MemoryStore(tmp_store_dir)
    assert tmp_store_dir.exists()


def test_store_creates_default_files(tmp_store_dir: Path) -> None:
    MemoryStore(tmp_store_dir)
    assert (tmp_store_dir / "preferences.md").exists()
    assert (tmp_store_dir / "facts.md").exists()
    assert (tmp_store_dir / "corrections.md").exists()


def test_write_and_read_entry(tmp_store_dir: Path) -> None:
    store = MemoryStore(tmp_store_dir)
    entry = MemoryEntry(
        content="Prefers concise answers",
        category="preferences",
        source_tool="claude",
        timestamp="2026-03-03T10:00:00",
    )
    store.write(entry)
    entries = store.read("preferences")
    assert len(entries) == 1
    assert entries[0].content == "Prefers concise answers"
    assert entries[0].source_tool == "claude"


def test_read_all_returns_all_categories(tmp_store_dir: Path) -> None:
    store = MemoryStore(tmp_store_dir)
    store.write(MemoryEntry("pref", "preferences", "claude", "2026-03-03T10:00:00"))
    store.write(MemoryEntry("fact", "facts", "gpt", "2026-03-03T10:01:00"))
    all_entries = store.read_all()
    assert len(all_entries) == 2


def test_search_returns_matching_entries(tmp_store_dir: Path) -> None:
    store = MemoryStore(tmp_store_dir)
    store.write(
        MemoryEntry(
            "Prefers Python over JavaScript",
            "preferences",
            "claude",
            "2026-03-03T10:00:00",
        )
    )
    store.write(
        MemoryEntry("Lives in San Jose", "facts", "claude", "2026-03-03T10:01:00")
    )
    results = store.search("Python")
    assert len(results) == 1
    assert "Python" in results[0].content


def test_search_is_case_insensitive(tmp_store_dir: Path) -> None:
    store = MemoryStore(tmp_store_dir)
    store.write(
        MemoryEntry("Prefers Python", "preferences", "claude", "2026-03-03T10:00:00")
    )
    results = store.search("python")
    assert len(results) == 1


def test_forget_removes_matching_entries(tmp_store_dir: Path) -> None:
    store = MemoryStore(tmp_store_dir)
    store.write(
        MemoryEntry("Prefers Python", "preferences", "claude", "2026-03-03T10:00:00")
    )
    store.write(
        MemoryEntry("Prefers dark mode", "preferences", "claude", "2026-03-03T10:01:00")
    )
    removed = store.forget("Python")
    assert removed == 1
    remaining = store.read("preferences")
    assert len(remaining) == 1
    assert "dark mode" in remaining[0].content


def test_read_empty_store_returns_empty_list(tmp_store_dir: Path) -> None:
    store = MemoryStore(tmp_store_dir)
    assert store.read("preferences") == []
    assert store.read_all() == []


def test_forget_does_not_match_source_tool_name(tmp_store_dir: Path) -> None:
    store = MemoryStore(tmp_store_dir)
    store.write(
        MemoryEntry("Prefers Python", "preferences", "claude", "2026-03-03T10:00:00")
    )
    # "claude" is the source_tool, not in content — should NOT be removed
    removed = store.forget("claude")
    assert removed == 0
    assert len(store.read("preferences")) == 1


def test_forget_zero_matches_returns_zero(tmp_store_dir: Path) -> None:
    store = MemoryStore(tmp_store_dir)
    store.write(
        MemoryEntry("Prefers Python", "preferences", "claude", "2026-03-03T10:00:00")
    )
    removed = store.forget("nonexistent_pattern_xyz")
    assert removed == 0
