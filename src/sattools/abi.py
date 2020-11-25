"""Tools related to reading ABI."""

import collections.abc

import appdirs
import s3fs
import fsspec.implementations.cached

import satpy
from typhon.files.fileset import FileSet

def get_fs_and_files(start_date, end_date, sector="F", chans=14):
    """Return filesystem object and files for ABI for period.

    Sector can be "C", "F", "M1", or "M2".

    Chans is a channel number or an array of channel numbers.
    """

    cachedir = appdirs.user_cache_dir("ABI-block-cache")

    if not isinstance(chans, collections.abc.Iterable):
        chans = {chans}

    fs_s3 = s3fs.S3FileSystem(anon=True)

    fs_block = fsspec.implementations.cached.CachingFileSystem(
            fs=fs_s3,
            cache_storage=cachedir,
            cache_check=600,
            check_files=False,
            expiry_times=False,
            same_names=False)

    # satpy can't search recursively, only directly in the same directory
    # therefore use typhon, and filter channels manually later
    abi_fileset = FileSet(
            path=f"noaa-goes16/ABI-L1b-Rad{sector[0]:s}/"
                 "{year}/{doy}/{hour}/"
                 f"OR_ABI-L1b-Rad{sector:s}-M6C*_G16_"
                 "s{year}{doy}{hour}{minute}{second}*_e{end_year}{end_doy}"
                 "{end_hour}{end_minute}{end_second}*_c*.nc",
            name="abi",
            fs=fs_s3)
    files = list(
            fi for fi in abi_fileset.find(start_date, end_date)
            if any(f"C{c:>02d}_" in fi.path for c in chans))
    return (fs_block, files)


def split_meso(ms):
    """Split a meso-multiscene into smaller multiscenes.

    Split a multiscene where the scenes have MESO areas that vary into smaller
    subset multiscenes where the MESO area is constant.

    Assumes this happens at the same scene for all channels.
    """

    # NB: https://github.com/pytroll/satpy/issues/1419
    ch = next(iter(ms.first_scene.keys()))
    ref = ms.first_scene[ch].attrs["area"]
    prev = 0
    for (i, sc) in enumerate(ms.scenes):
        if (newref := sc[ch].attrs["area"]) != ref:
            yield satpy.MultiScene(ms.scenes[prev:i])
            ref = newref
            prev = i
    yield satpy.MultiScene(ms.scenes[prev:])
