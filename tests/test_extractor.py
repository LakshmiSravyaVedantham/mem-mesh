from unittest.mock import MagicMock

from anthropic.types import TextBlock

from mem_mesh.extractor import MemoryExtractor
from mem_mesh.store import MemoryEntry

FIXTURE_MESSAGES = [
    {
        "role": "user",
        "content": "I always prefer Python over JavaScript. Don't suggest JS.",
    },
    {"role": "assistant", "content": "Got it, I'll stick to Python."},
    {"role": "user", "content": "Also, I live in San Jose and work at a startup."},
    {"role": "assistant", "content": "Noted."},
]


def _make_mock_client(json_response: str) -> MagicMock:
    mock_client = MagicMock()
    mock_content = MagicMock(spec=TextBlock)
    mock_content.text = json_response
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_client.messages.create.return_value = mock_response
    return mock_client


def test_extract_returns_list() -> None:
    mock_client = _make_mock_client(
        '[{"content": "Prefers Python", "category": "preferences"}]'
    )
    extractor = MemoryExtractor(client=mock_client)
    result = extractor.extract(FIXTURE_MESSAGES)
    assert isinstance(result, list)


def test_extract_returns_memory_entries() -> None:
    mock_client = _make_mock_client(
        '[{"content": "Prefers Python over JavaScript", "category": "preferences"}]'
    )
    extractor = MemoryExtractor(client=mock_client)
    result = extractor.extract(FIXTURE_MESSAGES, source_tool="claude")
    assert len(result) == 1
    assert isinstance(result[0], MemoryEntry)
    assert result[0].category == "preferences"
    assert result[0].source_tool == "claude"
    assert "Python" in result[0].content


def test_extract_returns_empty_on_empty_messages() -> None:
    mock_client = MagicMock()
    extractor = MemoryExtractor(client=mock_client)
    result = extractor.extract([])
    assert result == []
    mock_client.messages.create.assert_not_called()


def test_extract_returns_empty_on_invalid_json() -> None:
    mock_client = _make_mock_client("not valid json")
    extractor = MemoryExtractor(client=mock_client)
    result = extractor.extract(FIXTURE_MESSAGES)
    assert result == []


def test_extract_filters_invalid_categories() -> None:
    mock_client = _make_mock_client(
        '[{"content": "something", "category": "invalid_category"}]'
    )
    extractor = MemoryExtractor(client=mock_client)
    result = extractor.extract(FIXTURE_MESSAGES)
    assert result == []


def test_extract_timestamps_are_set() -> None:
    mock_client = _make_mock_client(
        '[{"content": "Prefers Python", "category": "preferences"}]'
    )
    extractor = MemoryExtractor(client=mock_client)
    result = extractor.extract(FIXTURE_MESSAGES)
    assert result[0].timestamp != ""


def test_extract_returns_empty_on_non_text_response() -> None:
    """Guard against non-text blocks (e.g. tool_use) in response."""
    mock_client = MagicMock()
    mock_block = MagicMock(spec=[])  # spec=[] means no attributes at all
    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_client.messages.create.return_value = mock_response
    extractor = MemoryExtractor(client=mock_client)
    result = extractor.extract(FIXTURE_MESSAGES)
    assert result == []
