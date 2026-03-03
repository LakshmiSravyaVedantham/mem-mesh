"""Entry point for running the proxy server as a subprocess (used by daemon)."""
from __future__ import annotations

import argparse

import uvicorn

from mem_mesh.proxy import build_app


def main() -> None:
    parser = argparse.ArgumentParser(description="mem-mesh proxy server")
    parser.add_argument("--port", type=int, default=4117)
    parser.add_argument("--target", default="https://api.anthropic.com")
    args = parser.parse_args()

    app = build_app(target_url=args.target)
    uvicorn.run(app, host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
