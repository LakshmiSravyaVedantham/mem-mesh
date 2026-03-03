import click

from mem_mesh import __version__


@click.group()
@click.version_option(version=__version__)
def cli() -> None:
    """mem-mesh — universal AI memory layer across all your AI tools."""
    pass
