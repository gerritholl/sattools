"""Various IO-related tools
"""
import os
import pathlib
import datetime


def get_cache_dir(base=None, subdir=""):
    """Get directory to use for caching

    Get (and create, if necessary) directory to use for caching.

    Args:
        base (str or pathlib.Path):
            Directory in which to create cache dir.  If not given, use
            XDG_CACHE_HOME or otherwise ~/.cache.
        subdir (Optional[str]):
            Subdirectory within cache-dir

    Returns:
        pathlib.Path object pointing to cache dir
    """
    cacheroot = (base or
                 os.environ.get("XDG_CACHE_HOME") or
                 pathlib.Path.home() / ".cache")
    cacheroot = pathlib.Path(cacheroot)
    cacheroot /= subdir
    return cacheroot


def plotdir():
    pd = pathlib.Path("/media/nas/x21308/plots_and_maps/" +
                      datetime.datetime.now().strftime("%Y/%m/%d"))
    return pd
