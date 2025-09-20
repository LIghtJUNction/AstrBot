import warnings

from ..updater import PluginUpdater as _PluginUpdater


class PluginUpdator(_PluginUpdater):
    """
    [DEPRECATED] This class has been renamed to PluginUpdater.
    Please use PluginUpdater instead. This alias will be removed in a future version.
    """

    def __init__(self, repo_mirror: str = "") -> None:
        warnings.warn(
            "PluginUpdator is deprecated and will be removed in a future version. "
            "Please use PluginUpdater instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(repo_mirror)
