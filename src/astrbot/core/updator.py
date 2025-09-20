import os
import psutil
import sys
import time
import warnings
from .zip_updator import ReleaseInfo, RepoZipUpdator
from .updater import AstrBotUpdater as _AstrBotUpdater
from astrbot.core import logger
from astrbot.core.config.default import VERSION
from typing import Any
from astrbot.core.utils.io import download_file
from astrbot.core.utils.astrbot_path import get_astrbot_path


class AstrBotUpdator(_AstrBotUpdater):
    """
    [DEPRECATED] This class has been renamed to AstrBotUpdater.
    Please use AstrBotUpdater instead. This alias will be removed in a future version.
    """

    def __init__(self, repo_mirror: str = "") -> None:
        warnings.warn(
            "AstrBotUpdator is deprecated and will be removed in a future version. "
            "Please use AstrBotUpdater instead.",
            DeprecationWarning,
            stacklevel=2,
        )

