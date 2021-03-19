"""Routines interacting with GLM and glmtools."""
import pathlib
import importlib

import appdirs
import pandas
import s3fs
import fsspec.implementations.cached
import logging
import os

from typhon.files.fileset import FileSet
from . import tputil

pattern_s3_glm_lcfa = (
        "noaa-goes16/GLM-L2-LCFA/{year}/{doy}/{hour}/"
        "OR_GLM-L2-LCFA_G16_s{year}{doy}{hour}{minute}{second}*_"
        "e{end_year}{end_doy}{end_hour}{end_minute}{end_second}*_c*.nc")

glm_script = "/home/gholl/checkouts/glmtools/examples/grid/make_GLM_grids.py"

logger = logging.getLogger(__name__)


def get_dwd_glm_basedir(sector="C", lat=None, lon=None, period="1min"):
    """Return the directory where processed GLM data shall be stored."""
    base = os.environ["NAS_DATA"]
    if sector not in ("C", "F", "M1", "M2"):
        raise ValueError(f"Invalid sector: {sector!s}. "
                         "Expected 'C', 'F', 'M1', or 'M2'.")
    bd = pathlib.Path(base) / "GLM-processed"
    bd /= sector
    if sector.startswith("M"):
        bd /= f"{lat:.1f}_{lon:.1f}"
    return bd / period


def get_pattern_dwd_glm(sector="C", lat=None, lon=None, period="1min"):
    """Return filename pattern for storing processed GLM data."""
    bd = get_dwd_glm_basedir(sector=sector, lat=lat, lon=lon, period=period)
    seclab = sector if sector in ("C", "F", "M1") else "M1"
    return str(bd /
               "{year}/{month}/{day}/{hour}/"
               f"OR_GLM-L2-GLM{seclab:s}-M3_G16_"
               "s{year}{doy}{hour}{minute}{second}*_"
               "e{end_year}{end_doy}{end_hour}{end_minute}{end_second}*_"
               "c*.nc")


def ensure_glm_lcfa_for_period(start_date, end_date):
    """Make sure GLM LCFA files for period are present locally.

    Yields the local paths for the (cached or downloaded) files.
    """
    logger.debug(
            "Ensuring local LCFA availability "
            f"{start_date:%Y-%m-%d %H:%M:%S}--{end_date:%H:%M:%S}")
    cachedir = appdirs.user_cache_dir("GLM-file-cache")
    s3 = s3fs.S3FileSystem(anon=True)
    wfcfs = fsspec.implementations.cached.WholeFileCacheFileSystem(
            fs=s3,
            cache_storage=cachedir,
            cache_check=86400,
            check_files=False,
            expiry_time=False,
            same_names=True)

    glm_lcfa = FileSet(path=pattern_s3_glm_lcfa, name="glm_lcfa", fs=s3)
    for f in glm_lcfa.find(start_date, end_date):
        if not f.times[1] > start_date:  # typhon uses closed intervals
            continue
        logger.debug(f"Downloading {f!s}")
        with wfcfs.open(f, mode="rb"):  # force download
            exp = pathlib.Path(cachedir) / pathlib.Path(f).name
            logger.debug(f"Writing to {exp!s}")
            # Is this guaranteed?  See
            # https://stackoverflow.com/q/64261276/974555
            if not exp.exists():
                raise FileNotFoundError(f"Not found! {exp!s}")
        yield exp


def ensure_glm_for_period(
        start_date, end_date, sector="C", lat=None, lon=None):
    """Get gridded GLM for period, unless already existing.

    Yields resulting GLM files as FSPath objects.
    """
    logger.debug(
            "Locating GLM gaps between "
            f"{start_date:%Y-%m-%d %H:%M:%S}--{end_date:%H:%M:%S}, "
            f"sector {sector:s}")
    for gap in find_glm_coverage_gaps(start_date, end_date, sector=sector,
                                      lat=lat, lon=lon):
        logger.debug(
                "Found gap between "
                f"{start_date:%Y-%m-%d %H:%M:%S}--{end_date:%H:%M:%S}")
        files = list(ensure_glm_lcfa_for_period(gap.left, gap.right))
        if sector in "CF":
            run_glmtools(files, max_files=60, sector=sector)
        else:
            run_glmtools(files, max_files=60, sector=sector,
                         lat=lat, lon=lon)
            logger.debug(f"GLM {sector:s} should now be fully covered")
    # there should be no more gaps now!
    for gap in find_glm_coverage_gaps(
            start_date, end_date, sector=sector, lat=lat, lon=lon):
        raise RuntimeError(
                f"I have tried to ensure GLM {sector:s} by running glmtools, "
                "but data still appear to be missing for "
                f"{start_date:%Y-%m-%d %H:%M:%S}--{end_date:%H:%M:%S} :( ")
    if sector in "CF":
        pat = get_pattern_dwd_glm(sector)
    else:
        pat = get_pattern_dwd_glm(sector, lat=lat, lon=lon)
    glm = FileSet(path=pat, name="glm")
    for fileinfo in glm.find(start_date, end_date, no_files_error=True):
        yield tputil.fileinfo2fspath(fileinfo)


def find_glm_coverage(start_date, end_date, sector="C", lat=None, lon=None):
    """Yield intervals corresponding to GLMC coverage."""
    if sector in "CF":
        pat = get_pattern_dwd_glm(sector)
    else:
        pat = get_pattern_dwd_glm(sector, lat=lat, lon=lon)
    glm = FileSet(path=pat, name="glm")
    for file_info in glm.find(start_date, end_date, no_files_error=False):
        yield pandas.Interval(
                pandas.Timestamp(file_info.times[0]),
                pandas.Timestamp(file_info.times[1]))


def find_glm_coverage_gaps(start_date, end_date, sector="C",
                           lat=None, lon=None):
    """Yield intervals not covered by GLMC in period."""
    last = pandas.Timestamp(start_date)
    for iv in find_glm_coverage(start_date, end_date, sector=sector,
                                lat=lat, lon=lon):
        if iv.left > last:
            yield pandas.Interval(last, iv.left)
        last = iv.right
    if last < end_date:
        yield pandas.Interval(last, pandas.Timestamp(end_date))


def load_file(name, path):
    """Help to run glmtools by importing module from file."""
    # Source: https://stackoverflow.com/a/59937532/974555
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_glmtools(files, max_files=180, sector="C", lat=None, lon=None):
    """Run glmtools.

    This function runs glmtools.
    """
    # how to call this?  should not be needed as a subprocess, although maybe
    # advantageous to keep things separate, can I at least determine the
    # location for make_GLM_grids in a more portable manner?

    if len(files) > max_files:
        logger.info(f"Got {len(files):d} > {max_files:d} files, splitting...")
    idx = 0
    glmtool = load_file("glmtool", glm_script)
    parser = glmtool.create_parser()
    glm_names = {"C": "conus",
                 "M1": "meso",
                 "M2": "meso",
                 "F": "full"}
    while idx < len(files):
        these_files = files[idx:(idx+max_files)]
        logger.info("Running glmtools for " + ", ".join(
                    str(f) for f in these_files))
        arg_list = ["--fixed_grid", "--split_events",
                    "--goes_position", "east", "--goes_sector",
                    glm_names[sector],
                    "--dx=2.0", "--dy=2.0", "--dt", "60"]
        if glm_names[sector] == "meso":
            arg_list.extend(["--ctr_lat", f"{lat:.2f}", "--ctr_lon",
                             f"{lon:.2f}"])
            outdir = get_dwd_glm_basedir(sector=sector, lat=lat, lon=lon)
        else:
            outdir = get_dwd_glm_basedir(sector=sector)
        arg_list.extend([
            "-o", str(outdir) +
            "/{start_time:%Y/%m/%d/%H}/{dataset_name}",
            *(str(f) for f in these_files)])
        args = parser.parse_args(arg_list)
        # this part taken from glmtools example script glm_script
        (gridder, glm_filenames, start_time, end_time, grid_kwargs) = \
            glmtool.grid_setup(args)
        gridder(glm_filenames, start_time, end_time, **grid_kwargs)

        idx += max_files
