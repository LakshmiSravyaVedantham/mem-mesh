from pathlib import Path

import pytest


@pytest.fixture
def tmp_store_dir(tmp_path: Path) -> Path:
    """Provides a temporary path for MemoryStore in tests.

    NOTE: The directory does NOT exist yet — MemoryStore.__init__ is expected
    to create it via mkdir(parents=True, exist_ok=True). Do not pre-create it.
    """
    return tmp_path / "mem-mesh"
