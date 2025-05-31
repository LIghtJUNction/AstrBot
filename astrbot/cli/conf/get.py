import click

@click.command()
@click.argument("key", required=False)
def get(key: str = None):
    """获取配置项的值，不提供key则显示所有可配置项"""
    from .utils import load_config, get_nested_item, CONFIG_VALIDATORS
    config = load_config()

    if key:
        if key not in CONFIG_VALIDATORS.keys():
            raise click.ClickException(f"不支持的配置项: {key}")

        try:
            value = get_nested_item(config, key)
            if key == "dashboard.password":
                value = "********"
            click.echo(f"{key}: {value}")
        except KeyError:
            raise click.ClickException(f"未知的配置项: {key}")
        except Exception as e:
            raise click.UsageError(f"获取配置失败: {str(e)}")
    else:
        click.echo("当前配置:")
        for key in CONFIG_VALIDATORS.keys():
            try:
                value = (
                    "********"
                    if key == "dashboard.password"
                    else get_nested_item(config, key)
                )
                click.echo(f"  {key}: {value}")
            except (KeyError, TypeError):
                pass