# mem-mesh

Universal AI memory layer. One persistent memory for all your AI tools — Claude, ChatGPT, Cursor, Copilot, Gemini.

[![CI](https://github.com/LakshmiSravyaVedantham/mem-mesh/actions/workflows/ci.yml/badge.svg)](https://github.com/LakshmiSravyaVedantham/mem-mesh/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/mem-mesh)](https://pypi.org/project/mem-mesh/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## The Problem

Every AI tool stores memory in isolation. Claude knows your preferences, but ChatGPT doesn't. Cursor doesn't know what Copilot learned. Every new tool starts from scratch.

## The Solution

mem-mesh is a local proxy that sits between you and every AI API. It intercepts your calls, injects your memories, and learns new ones — transparently, across all tools.

Your data lives in `~/.mem-mesh/` as plain Markdown. Readable, Git-backable, yours forever.

## Quickstart

```bash
pip install mem-mesh

# Start the proxy
mem-mesh daemon start

# Set the env var once — add to ~/.zshrc or ~/.bashrc
export ANTHROPIC_BASE_URL=http://localhost:4117

# Use any AI tool normally — memory builds automatically
```

## How It Works

```
Your AI tool ──► ANTHROPIC_BASE_URL=localhost:4117 ──► mem-mesh proxy
                      │
                      ├── injects stored memories into system prompt
                      ├── forwards request to real Anthropic API
                      └── on response: extracts new memory signals (async)
                                             │
                                             └── stores in ~/.mem-mesh/*.md
```

## CLI Reference

```bash
# Daemon
mem-mesh daemon start [--port 4117]    # Start proxy in background
mem-mesh daemon stop                   # Stop proxy
mem-mesh daemon status                 # Check status

# Memory
mem-mesh show                          # Show all memories
mem-mesh show --category preferences   # Show one category
mem-mesh search "Python"               # Search memories
mem-mesh forget "JavaScript"           # Remove matching memories
```

## Memory Format

Plain Markdown, one entry per line:

```
~/.mem-mesh/
  preferences.md    # - [2026-03-03T10:00:00] (claude) Prefers Python over JavaScript
  facts.md          # - [2026-03-03T10:01:00] (cursor) Lives in San Jose
  corrections.md    # - [2026-03-03T10:02:00] (claude) Function is get_user not fetch_user
```

## Privacy

- Runs 100% locally. Nothing is sent to any server besides your configured AI provider.
- All memory is stored in `~/.mem-mesh/` — inspect, edit, or delete any time.
- `mem-mesh forget "pattern"` removes entries matching a pattern.

## Works With Any OpenAI-Compatible API

mem-mesh intercepts any API that accepts the standard messages format. Set the base URL in whatever tool you're using:

```bash
export ANTHROPIC_BASE_URL=http://localhost:4117    # Claude / Anthropic SDK
export OPENAI_BASE_URL=http://localhost:4117       # OpenAI SDK
```

## Development

```bash
git clone https://github.com/LakshmiSravyaVedantham/mem-mesh
cd mem-mesh
python3 -m venv venv && source venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

MIT
