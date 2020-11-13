import pathlib
import datetime
import logging

from unittest.mock import patch, call, MagicMock

import pandas
import pytest
from conftest import _mk_test_files


@patch("appdirs.user_cache_dir")
@patch("s3fs.S3FileSystem")
def test_ensure_glm_lcfa(sS, au, lcfa_pattern, lcfa_files, tmp_path, caplog):
    from sattools.glm import ensure_glm_lcfa_for_period
    from fsspec.implementations.local import LocalFileSystem
    from typhon.files.fileset import NoFilesError
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
        with caplog.at_level(logging.DEBUG):
            files = list(ensure_glm_lcfa_for_period(
                    datetime.datetime(1900, 1, 1, 0, 0, 0),
                    datetime.datetime(1900, 1, 1, 0, 6, 0)))
        assert (f"Downloading {tmp_path!s}/lcfa-fake/"
                f"lcfa-fake-19000101000000-000100.nc" in caplog.text)
        assert (f"Writing to {tmp_path!s}/"
                f"whole-file-cache/lcfa-fake-19000101000000-000100.nc" in
                caplog.text)
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
        with pytest.raises(NoFilesError):
            next(ensure_glm_lcfa_for_period(
                    datetime.datetime(1900, 1, 2, 0, 0, 0),
                    datetime.datetime(1900, 1, 2, 0, 1, 0)))


@patch("sattools.glm.run_glmtools")
@patch("appdirs.user_cache_dir")
@patch("s3fs.S3FileSystem")
def test_ensure_glmc(sS, au, sgr, glmc_pattern, glmc_files, lcfa_pattern,
                     lcfa_files, tmp_path):
    from sattools.glm import ensure_glmc_for_period
    from fsspec.implementations.local import LocalFileSystem
    from typhon.files.fileset import FileInfo
    au.return_value = str(tmp_path / "whole-file-cache")
    sS.return_value = LocalFileSystem()
    with patch("sattools.glm.pattern_dwd_glm_glmc", glmc_pattern), \
         patch("sattools.glm.pattern_s3_glm_lcfa", lcfa_pattern):
        with pytest.raises(RuntimeError):  # files not created when testing
            next(ensure_glmc_for_period(
                    datetime.datetime(1900, 1, 1, 0, 0, 0),
                    datetime.datetime(1900, 1, 1, 0, 6, 0)))
        sgr.assert_has_calls(
                [call([tmp_path / "whole-file-cache" /
                       f"lcfa-fake-1900010100{m:>02d}00-00{m+1:>02d}00.nc"],
                      max_files=60)
                 for m in (2, 4)])

        def fake_run(files, max_files):
            """Create files when testing."""
            _mk_test_files(glmc_pattern, (0, 1, 2, 3, 4, 5, 6))
        sgr.side_effect = fake_run
        g = ensure_glmc_for_period(
                datetime.datetime(1900, 1, 1, 0, 0, 0),
                datetime.datetime(1900, 1, 1, 0, 6, 0))
        fi = next(g)
        assert isinstance(fi, FileInfo)
        assert fi.path == str(tmp_path / "glmc-fake" /
               "glmc-fake-19000101000000-000100.nc")
        assert fi.times == [datetime.datetime(1900, 1, 1, 0, 0),
                            datetime.datetime(1900, 1, 1, 0, 1)]


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
        gaps = list(find_glmc_coverage_gaps(
            datetime.datetime(1900, 1, 2, 0, 0),
            datetime.datetime(1900, 1, 2, 0, 8)))
        assert gaps == [
                pandas.Interval(pandas.Timestamp("1900-01-02T00:00:00"),
                                pandas.Timestamp("1900-01-02T00:08:00"))]
        gaps = list(find_glmc_coverage_gaps(
            datetime.datetime(1900, 1, 1, 0, 0),
            datetime.datetime(1900, 1, 1, 0, 2)))
        assert list(gaps) == []


def test_run_glmtools(tmp_path, caplog):
    from sattools.glm import run_glmtools
    with patch("sattools.glm.load_file") as sgl:
        mocks = [MagicMock() for _ in range(5)]
        sgl.return_value.grid_setup.return_value = mocks
        with caplog.at_level(logging.INFO):
            run_glmtools([tmp_path / "lcfa1.nc", tmp_path / "lcfa2.nc"])
            assert (f"Running glmtools for {(tmp_path / 'lcfa1.nc')!s}, "
                    f"{(tmp_path / 'lcfa2.nc')!s}" in caplog.text)
        mocks[0].assert_called_once()
        mocks[0].reset_mock()
        run_glmtools([tmp_path / "lcfa1.nc", tmp_path / "lcfa2.nc"],
                     max_files=1)
        assert mocks[0].call_count == 2
