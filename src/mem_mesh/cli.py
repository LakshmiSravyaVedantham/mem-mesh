from __future__ import annotations

import click

from mem_mesh import __version__
from mem_mesh.daemon import Daemon
from mem_mesh.store import MemoryStore


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """mem-mesh — universal AI memory layer across all your AI tools."""


# ── Daemon commands ──────────────────────────────────────────────────────────


@cli.group()
def daemon() -> None:
    """Manage the mem-mesh proxy daemon."""


@daemon.command("start")
@click.option("--port", default=4117, show_default=True, help="Proxy port")
@click.option(
    "--target",
    default="https://api.anthropic.com",
    show_default=True,
    help="Real API base URL to forward to",
)
def daemon_start(port: int, target: str) -> None:
    """Start the proxy daemon in the background."""
    pid = Daemon.start(port=port, target_url=target)
    click.echo(f"Daemon started (PID {pid})")
    click.echo(f"\nSet this env var to route AI calls through mem-mesh:")
    click.echo(f"  export ANTHROPIC_BASE_URL=http://localhost:{port}")


@daemon.command("stop")
def daemon_stop() -> None:
    """Stop the proxy daemon."""
    if Daemon.stop():
        click.echo("Daemon stopped.")
    else:
        click.echo("Daemon is not running.")


@daemon.command("status")
def daemon_status() -> None:
    """Show daemon status."""
    if Daemon.is_running():
        click.echo(f"Running (PID {Daemon.get_pid()})")
    else:
        click.echo("Stopped")


# ── Memory commands ──────────────────────────────────────────────────────────


@cli.command("show")
@click.option(
    "--category",
    type=click.Choice(["preferences", "facts", "corrections", "all"]),
    default="all",
    show_default=True,
)
def show(category: str) -> None:
    """Show stored memories."""
    store = MemoryStore()
    entries = store.read(category) if category != "all" else store.read_all()
    if not entries:
        click.echo("No memories yet. Start the daemon and use an AI tool to build memory.")
        return
    current_cat = None
    for entry in entries:
        if entry.category != current_cat:
            current_cat = entry.category
            click.echo(f"\n[{current_cat.upper()}]")
        click.echo(f"  {entry.content}  ({entry.source_tool}, {entry.timestamp[:10]})")


@cli.command("search")
@click.argument("query")
def search(query: str) -> None:
    """Search memories for a keyword."""
    store = MemoryStore()
    results = store.search(query)
    if not results:
        click.echo(f"No memories matching '{query}'")
        return
    for entry in results:
        click.echo(f"[{entry.category}] {entry.content}")


@cli.command("forget")
@click.argument("pattern")
@click.option("--yes", is_flag=True, help="Skip confirmation prompt")
def forget(pattern: str, yes: bool) -> None:
    """Remove memories matching a pattern."""
    store = MemoryStore()
    if not yes:
        click.confirm(f"Remove all memories matching '{pattern}'?", abort=True)
    removed = store.forget(pattern)
    click.echo(f"Removed {removed} {'entry' if removed == 1 else 'entries'}.")
