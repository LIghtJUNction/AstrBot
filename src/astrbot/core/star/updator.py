import os
import zipfile
import shutil
import warnings

from ..updator import RepoZipUpdator
from ..updater import PluginUpdater as _PluginUpdater
from astrbot.core.utils.io import remove_dir, on_error
from ..star.star import StarMetadata
from astrbot.core import logger
from astrbot.core.utils.astrbot_path import get_astrbot_plugin_path


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

