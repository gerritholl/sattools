"""Tools related to reading ABI."""

import appdirs
import s3fs
import fsspec.implementations.cached
from typhon.files.fileset import FileSet


def get_fs_and_files(start_date, end_date, sector="F"):
    """Return filesystem object and files for ABI for period.

    Sector can be "C", "F", "M1", or "M2".
    """

    cachedir = appdirs.user_cache_dir("ABI-block-cache")

    fs_s3 = s3fs.S3FileSystem(anon=True)

    fs_block = fsspec.implementations.cached.CachingFileSystem(
            fs=fs_s3,
            cache_storage=cachedir,
            cache_check=600,
            check_files=False,
            expiry_times=False,
            same_names=False)

    # satpy can't search recursively, only directly in the same directory
    # therefore use typhon
    abi_fileset = FileSet(
            path=f"noaa-goes16/ABI-L1b-Rad{sector:s}/"
                 "{year}/{doy}/{hour}/"
                 f"OR_ABI-L1b-Rad{sector:s}-M6C*_G16_"
                 "s{year}{doy}{hour}{minute}{second}*_e{end_year}{end_doy}"
                 "{end_hour}{end_minute}{end_second}*_c*.nc",
            name="abi",
            fs=fs_s3)
    files = list(abi_fileset.find(start_date, end_date))
    return (fs_block, files)
