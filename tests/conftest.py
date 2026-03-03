import pytest
from pathlib import Path


@pytest.fixture
def tmp_store_dir(tmp_path: Path) -> Path:
    """Provides a temporary directory for MemoryStore in tests."""
    return tmp_path / "mem-mesh"
