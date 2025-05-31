from typing import Callable , Any
import click

@click.command("set")
@click.argument("key")
@click.argument("value")
def set_config(key: str, value: str):
    """设置配置项的值"""
    from .utils import load_config, save_config, get_nested_item, set_nested_item
    from ..utils import (
        validate_timezone,
        validate_log_level,
        validate_dashboard_port,
        validate_dashboard_username,
        validate_dashboard_password,
        validate_callback_api_base,
    )
    # 可通过CLI设置的配置项，配置键到验证器函数的映射
    CONFIG_VALIDATORS: dict[str, Callable[[str], Any]] = {
        "timezone": validate_timezone,
        "log_level": validate_log_level,
        "dashboard.port": validate_dashboard_port,
        "dashboard.username": validate_dashboard_username,
        "dashboard.password": validate_dashboard_password,
        "callback_api_base": validate_callback_api_base,
    }


    if key not in CONFIG_VALIDATORS.keys():
        raise click.ClickException(f"不支持的配置项: {key}")

    config = load_config()

    try:
        old_value = get_nested_item(config, key)
        validated_value = CONFIG_VALIDATORS[key](value)
        set_nested_item(config, key, validated_value)
        save_config(config)

        click.echo(f"配置已更新: {key}")
        if key == "dashboard.password":
            click.echo("  原值: ********")
            click.echo("  新值: ********")
        else:
            click.echo(f"  原值: {old_value}")
            click.echo(f"  新值: {validated_value}")

    except KeyError:
        raise click.ClickException(f"未知的配置项: {key}")
    except Exception as e:
        raise click.UsageError(f"设置配置失败: {str(e)}")