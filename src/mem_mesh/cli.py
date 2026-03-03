import click


@click.group()
@click.version_option()
def cli() -> None:
    """mem-mesh — universal AI memory layer across all your AI tools."""
    pass
