import pathlib
import subprocess

import appdirs
import pandas
import s3fs
import fsspec.implementations.cached

from typhon.files.fileset import FileSet

pattern_s3_glm_lcfa = (
        "noaa-goes16/GLM-L2-LCFA/{year}/{doy}/{hour}/"
        "OR_GLM-L2-LCFA_G16_s{year}{doy}{hour}{minute}{second}*_"
        "e{end_year}{end_doy}{end_hour}{end_minute}{end_second}*_c*.nc")
pattern_dwd_glm_glmc_basedir = "/media/nas/x21308/GLM/GLMC/1min/"
pattern_dwd_glm_glmc = (
        pattern_dwd_glm_glmc_basedir +
        "{year}/{month}/{day}/{hour}/"
        "OR_GLM-L2-GLMC-M3_G16_s{year}{doy}{hour}{minute}{second}*_"
        "e{end_year}{end_doy}{end_hour}{end_minute}{end_second}*_"
        "c*.nc")
glm_script = "/home/gholl/checkouts/glmtools/examples/grid/make_GLM_grids.py"


def ensure_glm_lcfa_for_period(start_date, end_date):
    """Make sure GLM LCFA files for period are present locally.

    Yields the local paths for the (cached or downloaded) files.
    """

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
    for f in glm_lcfa.find(start_date, end_date, no_files_error=False):
        if not f.times[1] > start_date:  # typhon uses closed intervals
            continue
        with wfcfs.open(f, mode="rb"):  # force download
            exp = pathlib.Path(cachedir) / pathlib.Path(f).name
            # Is this guaranteed?  See
            # https://stackoverflow.com/q/64261276/974555
            if not exp.exists():
                raise FileNotFoundError(f"Not found! {exp!s}")
        yield exp


def ensure_glmc_for_period(start_date, end_date):
    """Get gridded GLM for period, unless already existing.
    """
    for gap in find_glmc_coverage_gaps(start_date, end_date):
        files = list(ensure_glm_lcfa_for_period(gap.left, gap.right))
        run_glmtools(files)
    # there should be no more gaps now!
    for gap in find_glmc_coverage_gaps(start_date, end_date):
        raise RuntimeError(
                "I have tried to ensure GLMC by running glmtools, but "
                "data still appear to be missing for "
                "{start_date:%Y-%m-%d %H:%M:%S}--{end_date:%H:%M:%S} :( ")

def find_glmc_coverage(start_date, end_date):
    """Yield intervals corresponding to GLMC coverage.
    """
    glmc = FileSet(path=pattern_dwd_glm_glmc, name="glmc")
    for file_info in glmc.find(start_date, end_date):
        yield pandas.Interval(
                pandas.Timestamp(file_info.times[0]),
                pandas.Timestamp(file_info.times[1]))


def find_glmc_coverage_gaps(start_date, end_date):
    """Yield intervals not covered by GLMC in period.
    """
    last = start_date
    for iv in find_glmc_coverage(start_date, end_date):
        if iv.left > last:
            yield pandas.Interval(last, iv.left)
        last = iv.right
    if last < end_date:
        yield pandas.Interval(last, pandas.Timestamp(end_date))


def run_glmtools(files):
    # how to call this?  should not be needed as a subprocess, although maybe
    # advantageous to keep things separate, can I at least determine the
    # location for make_GLM_grids in a more portable manner?

    # FIXME: Surely I can use a Python API for this call...
    subprocess.run(
            ["python", glm_script, "--fixed_grid", "--split_events",
             "--goes_position", "east", "--goes_sector", "conus", "--dx=2.0",
             "--dy=2.0", "--dt", "60", "-o",
             pattern_dwd_glm_glmc_basedir +
             "{start_time:%Y/%m/%d/%H}/{dataset_name}",
             [str(f) for f in files]],
            capture_output=True, shell=False, cwd=None, timeout=120,
            check=True)
