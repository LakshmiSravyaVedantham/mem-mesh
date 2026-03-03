from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path


class Daemon:
    _PID_FILE = Path.home() / ".mem-mesh" / "daemon.pid"

    @classmethod
    def start(
        cls, port: int = 4117, target_url: str = "https://api.anthropic.com"
    ) -> int:
        if cls.is_running():
            pid = cls._read_pid()
            assert pid is not None
            return pid

        cls._PID_FILE.parent.mkdir(parents=True, exist_ok=True)

        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "mem_mesh._runner",
                "--port",
                str(port),
                "--target",
                target_url,
            ],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls._PID_FILE.write_text(str(proc.pid))
        return proc.pid

    @classmethod
    def stop(cls) -> bool:
        if not cls.is_running():
            return False
        pid = cls._read_pid()
        if pid is None:
            return False
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        cls._PID_FILE.unlink(missing_ok=True)
        return True

    @classmethod
    def is_running(cls) -> bool:
        pid = cls._read_pid()
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            cls._PID_FILE.unlink(missing_ok=True)
            return False

    @classmethod
    def get_pid(cls) -> int | None:
        return cls._read_pid() if cls.is_running() else None

    @classmethod
    def _read_pid(cls) -> int | None:
        if not cls._PID_FILE.exists():
            return None
        try:
            return int(cls._PID_FILE.read_text().strip())
        except (ValueError, OSError):
            return None
