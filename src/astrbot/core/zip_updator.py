import warnings

# Import the new classes
from .zip_updater import ReleaseInfo as _ReleaseInfo, RepoZipUpdater as _RepoZipUpdater


# For backward compatibility - expose the original ReleaseInfo
ReleaseInfo = _ReleaseInfo


class RepoZipUpdator(_RepoZipUpdater):
    """
    [DEPRECATED] This class has been renamed to RepoZipUpdater.
    Please use RepoZipUpdater instead. This alias will be removed in a future version.
    """

    def __init__(self, repo_mirror: str = "") -> None:
        warnings.warn(
            "RepoZipUpdator is deprecated and will be removed in a future version. "
            "Please use RepoZipUpdater instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(repo_mirror)
