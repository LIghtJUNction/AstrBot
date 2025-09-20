from typing import Any

__version__ = "3.5.23"


def get_cli():
    """延迟导入CLI函数以避免循环导入问题"""
    from .__main__ import cli

    return cli


def __getattr__(name: str) -> Any:
    if name == "cli":
        return get_cli()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "__version__",
    "cli",
]
