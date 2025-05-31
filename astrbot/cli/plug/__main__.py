import click

@click.group()
def plug():
    """插件管理"""
    pass

from astrbot.cli.plug.new import new
from astrbot.cli.plug.search import search
from astrbot.cli.plug.list import list
from astrbot.cli.plug.install import install
from astrbot.cli.plug.update import update
from astrbot.cli.plug.remove import remove

plug.add_command(new)
plug.add_command(search)
plug.add_command(list)
plug.add_command(install)
plug.add_command(update)
plug.add_command(remove)


if __name__ == "__main__":
    plug()