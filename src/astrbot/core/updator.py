import warnings
from .updater import AstrBotUpdater as _AstrBotUpdater


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
        super().__init__(repo_mirror)
