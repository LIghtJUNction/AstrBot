import click

@click.command()
@click.argument("name")
def remove(name: str):
    """卸载插件"""
    import shutil
    from ..utils import get_astrbot_root, build_plug_list
    base_path = get_astrbot_root()
    plugins = build_plug_list(base_path / "plugins")
    plugin = next((p for p in plugins if p["name"] == name), None)

    if not plugin or not plugin.get("local_path"):
        raise click.ClickException(f"插件 {name} 不存在或未安装")

    plugin_path = plugin["local_path"]

    click.confirm(f"确定要卸载插件 {name} 吗?", default=False, abort=True)

    try:
        shutil.rmtree(plugin_path)
        click.echo(f"插件 {name} 已卸载")
    except Exception as e:
        raise click.ClickException(f"卸载插件 {name} 失败: {e}")
