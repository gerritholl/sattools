import pathlib
import datetime

from unittest.mock import patch, call

import pandas
import pytest


@pytest.fixture
def glmc_pattern(tmp_path):
    # typhon fileset doesn't understand the full format-specification
    # mini-language, so something like hour:>02d doesn't work...
    return str(tmp_path / "glmc-fake" /
               "glmc-fake-{year}{month}{day}{hour}{minute}{second}-"
               "{end_hour}{end_minute}{end_second}.nc")


@pytest.fixture
def lcfa_pattern(tmp_path):
    return str(tmp_path / "lcfa-fake" /
               "lcfa-fake-{year}{month}{day}{hour}{minute}{second}-"
               "{end_hour}{end_minute}{end_second}.nc")


def _mk_test_files(pattern, minutes):
    pat = pathlib.Path(pattern)
    pat.parent.mkdir(exist_ok=True, parents=True)
    files = []
    for m in minutes:
        # ...(see line 11-12) therefore I need to pass strings here
        p = pat.with_name(
                pat.name.format(
                    year="1900", month="01", day="01", hour="00",
                    minute=f"{m:>02d}", second="00",
                    end_hour="00", end_minute=f"{m+1:>02d}",
                    end_second="00"))
        p.touch()
        files.append(p)
    return files


@pytest.fixture
def glmc_files(glmc_pattern):
    return _mk_test_files(glmc_pattern, (0, 1, 3, 5))


@pytest.fixture
def lcfa_files(lcfa_pattern):
    return _mk_test_files(lcfa_pattern, (0, 1, 2, 3, 4, 5))


@patch("appdirs.user_cache_dir")
@patch("s3fs.S3FileSystem")
def test_ensure_glm_lcfa(sS, au, lcfa_pattern, lcfa_files, tmp_path):
    from sattools.glm import ensure_glm_lcfa_for_period
    from fsspec.implementations.local import LocalFileSystem
    au.return_value = str(tmp_path / "whole-file-cache")
    sS.return_value = LocalFileSystem()
    with patch("sattools.glm.pattern_s3_glm_lcfa", lcfa_pattern):
        # test that I'm raising a FileNotFoundError if unexpectedly no file
        # created where expected
        with patch("fsspec.implementations.cached.WholeFileCacheFileSystem"):
            with pytest.raises(FileNotFoundError):
                for _ in ensure_glm_lcfa_for_period(
                        datetime.datetime(1900, 1, 1, 0, 0, 0),
                        datetime.datetime(1900, 1, 1, 0, 6, 0)):
                    pass
        files = list(ensure_glm_lcfa_for_period(
                datetime.datetime(1900, 1, 1, 0, 0, 0),
                datetime.datetime(1900, 1, 1, 0, 6, 0)))
        assert len(files) == 6
        assert files == [
                pathlib.Path(
                    tmp_path / "whole-file-cache" /
                    f"lcfa-fake-1900010100{m:>02d}00-00{m+1:>02d}00.nc")
                for m in range(6)]
        for f in files:
            assert f.exists()
        files = list(ensure_glm_lcfa_for_period(
                datetime.datetime(1900, 1, 1, 0, 1, 0),
                datetime.datetime(1900, 1, 1, 0, 2, 0)))
        assert len(files) == 1
        assert files == [
                pathlib.Path(
                    tmp_path / "whole-file-cache" /
                    "lcfa-fake-19000101000100-000200.nc")]
        files = list(ensure_glm_lcfa_for_period(
                datetime.datetime(1900, 1, 2, 0, 0, 0),
                datetime.datetime(1900, 1, 2, 0, 1, 0)))
        assert len(files) == 0


@patch("sattools.glm.run_glmtools")
@patch("appdirs.user_cache_dir")
@patch("s3fs.S3FileSystem")
def test_ensure_glmc(sS, au, sgr, glmc_pattern, glmc_files, lcfa_pattern,
                     lcfa_files, tmp_path):
    from sattools.glm import ensure_glmc_for_period
    from fsspec.implementations.local import LocalFileSystem
    au.return_value = str(tmp_path / "whole-file-cache")
    sS.return_value = LocalFileSystem()
    with patch("sattools.glm.pattern_dwd_glm_glmc", glmc_pattern), \
         patch("sattools.glm.pattern_s3_glm_lcfa", lcfa_pattern):
        with pytest.raises(RuntimeError):  # files not created when just testing
            ensure_glmc_for_period(
                    datetime.datetime(1900, 1, 1, 0, 0, 0),
                    datetime.datetime(1900, 1, 1, 0, 6, 0))
        sgr.assert_has_calls(
                [call([tmp_path / "whole-file-cache" /
                       f"lcfa-fake-1900010100{m:>02d}00-00{m+1:>02d}00.nc"])
                 for m in (2, 4)])


def test_find_coverage(glmc_pattern, glmc_files):
    from sattools.glm import find_glmc_coverage
    with patch("sattools.glm.pattern_dwd_glm_glmc", glmc_pattern):
        covered = list(find_glmc_coverage(
            datetime.datetime(1900, 1, 1, 0, 0, 0),
            datetime.datetime(1900, 1, 1, 0, 6, 0)))
    assert covered == [
            pandas.Interval(pandas.Timestamp("1900-01-01T00:00:00"),
                            pandas.Timestamp("1900-01-01T00:01:00")),
            pandas.Interval(pandas.Timestamp("1900-01-01T00:01:00"),
                            pandas.Timestamp("1900-01-01T00:02:00")),
            pandas.Interval(pandas.Timestamp("1900-01-01T00:03:00"),
                            pandas.Timestamp("1900-01-01T00:04:00")),
            pandas.Interval(pandas.Timestamp("1900-01-01T00:05:00"),
                            pandas.Timestamp("1900-01-01T00:06:00"))]
    with patch("sattools.glm.pattern_dwd_glm_glmc", glmc_pattern):
        covered = list(find_glmc_coverage(
            datetime.datetime(1900, 1, 2, 3, 4, 5),
            datetime.datetime(1900, 5, 4, 3, 2, 1)))
        assert covered == []


def test_find_gaps(glmc_pattern, glmc_files):
    from sattools.glm import find_glmc_coverage_gaps
    with patch("sattools.glm.pattern_dwd_glm_glmc", glmc_pattern):
        gaps = list(find_glmc_coverage_gaps(
            datetime.datetime(1900, 1, 1, 0, 0),
            datetime.datetime(1900, 1, 1, 0, 8)))
    assert gaps == [
            pandas.Interval(pandas.Timestamp("1900-01-01T00:02:00"),
                            pandas.Timestamp("1900-01-01T00:03:00")),
            pandas.Interval(pandas.Timestamp("1900-01-01T00:04:00"),
                            pandas.Timestamp("1900-01-01T00:05:00")),
            pandas.Interval(pandas.Timestamp("1900-01-01T00:06:00"),
                            pandas.Timestamp("1900-01-01T00:08:00"))]


def test_run_glmtools(tmp_path):
    from sattools.glm import run_glmtools
    with patch("subprocess.run") as sr:
        run_glmtools([tmp_path / "lcfa1.nc", tmp_path / "lcfa2.nc"])
        sr.assert_called_once_with(
            ["python",
             "/home/gholl/checkouts/glmtools/examples/grid/make_GLM_grids.py",
             "--fixed_grid", "--split_events", "--goes_position", "east",
             "--goes_sector", "conus", "--dx=2.0", "--dy=2.0", "--dt", "60",
             "-o", "/media/nas/x21308/GLM/GLMC/1min/"
             "{start_time:%Y/%m/%d/%H}/{dataset_name}",
             [str(tmp_path / "lcfa1.nc"), str(tmp_path / "lcfa2.nc")]],
            capture_output=True, shell=False, cwd=None, timeout=120,
            check=True)
