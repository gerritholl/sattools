"""Test functionality related to glm module."""

import os
import pathlib
import datetime
import logging

from unittest.mock import patch, call, MagicMock

import numpy
import pandas
import pytest
from .conftest import _mk_test_files
from . import utils


def test_get_basedir(tmp_path, monkeypatch):
    """Test getting the GLM basedir."""
    from sattools.glm import get_dwd_glm_basedir
    monkeypatch.setenv("NAS_DATA", str(tmp_path / "nas"))
    for m in ("C", "F"):
        d = get_dwd_glm_basedir(m)
        assert d == pathlib.Path(tmp_path / "nas" / "GLM-processed" /
                                 f"{m:s}" / "1min")
    for m in ("M1", "M2"):
        d = get_dwd_glm_basedir(m, lat=45, lon=-55.3)
        assert d == pathlib.Path(tmp_path / "nas" / "GLM-processed" /
                                 f"{m:s}" / "45.0_-55.3" / "1min")
    with pytest.raises(ValueError):
        d = get_dwd_glm_basedir("invalid")


def test_get_pattern(tmp_path, monkeypatch):
    """Test getting GLM pattern."""
    from sattools.glm import get_pattern_dwd_glm
    monkeypatch.setenv("NAS_DATA", str(tmp_path / "nas"))
    for m in "CF":
        p = get_pattern_dwd_glm(m)
        assert p == str(pathlib.Path(
            tmp_path / "nas" / "GLM-processed" / f"{m:s}" / "1min"
            / "{year}/{month}/{day}/{hour}/"
            f"OR_GLM-L2-GLM{m:s}-M3_G16_"
            "s{year}{doy}{hour}{minute}{second}*_"
            "e{end_year}{end_doy}{end_hour}{end_minute}{end_second}*_c*.nc"))
    for i in (1, 2):
        # NB: until the fix for
        # https://github.com/deeplycloudy/glmtools/issues/73 the output
        # filenames always show M1 as the sector
        p = get_pattern_dwd_glm(f"M{i:d}", lat=45, lon=-55.3)
        assert p == str(pathlib.Path(
            tmp_path / "nas" / "GLM-processed" / f"M{i:d}" / "45.0_-55.3" /
            "1min" / "{year}/{month}/{day}/{hour}/"
            "OR_GLM-L2-GLMM1-M3_G16_"
            "s{year}{doy}{hour}{minute}{second}*_"
            "e{end_year}{end_doy}{end_hour}{end_minute}{end_second}*_c*.nc"))


@patch("appdirs.user_cache_dir")
@patch("s3fs.S3FileSystem")
def test_ensure_glm_lcfa(sS, au, lcfa_pattern, lcfa_files, tmp_path, caplog,
                         monkeypatch):
    """Test ensuring GLM LCFA is created."""
    from sattools.glm import ensure_glm_lcfa_for_period
    from fsspec.implementations.local import LocalFileSystem
    from typhon.files.fileset import NoFilesError
    monkeypatch.setenv("NAS_DATA", str(tmp_path / "nas"))
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
def test_ensure_glm(sS, au, sgr, glm_files, lcfa_pattern,
                    lcfa_files, tmp_path, monkeypatch):
    """Test ensuring GLM GLMC is calculated."""
    from sattools.glm import ensure_glm_for_period
    from sattools.glm import get_pattern_dwd_glm
    from fsspec.implementations.local import LocalFileSystem
    monkeypatch.setenv("NAS_DATA", str(tmp_path / "nas"))
    au.return_value = str(tmp_path / "whole-file-cache")
    sS.return_value = LocalFileSystem()
    with patch("sattools.glm.pattern_s3_glm_lcfa", lcfa_pattern):
        with pytest.raises(RuntimeError):  # files not created when testing
            next(ensure_glm_for_period(
                    datetime.datetime(1900, 1, 1, 0, 0, 0),
                    datetime.datetime(1900, 1, 1, 0, 6, 0),
                    sector="C"))
        sgr.assert_has_calls(
                [call([tmp_path / "whole-file-cache" /
                       f"lcfa-fake-1900010100{m:>02d}00-00{m+1:>02d}00.nc"],
                      max_files=60,
                      sector="C")
                 for m in (2, 4)])

        def fake_run(files, max_files, sector="C", lat=None, lon=None):
            """Create files when testing."""
            _mk_test_files(get_pattern_dwd_glm(sector, lat=lat, lon=lon),
                           (0, 1, 2, 3, 4, 5, 6))
        sgr.side_effect = fake_run
        g = ensure_glm_for_period(
                datetime.datetime(1900, 1, 1, 0, 0, 0),
                datetime.datetime(1900, 1, 1, 0, 6, 0),
                sector="C")
        fi = next(g)
        assert isinstance(fi, str)
        assert os.fspath(fi) == os.fspath(
                tmp_path / "nas" / "GLM-processed" / "C" /
                "1min" / "1900" / "01" / "01" / "00" /
                "OR_GLM-L2-GLMC-M3_G16_s1900001000000*_e1900001000100*_c*.nc")

        g = ensure_glm_for_period(
                datetime.datetime(1900, 1, 1, 0, 0, 0),
                datetime.datetime(1900, 1, 1, 0, 6, 0),
                sector="M1",
                lat=10,
                lon=20)
        fi = next(g)
        assert os.fspath(fi) == os.fspath(
                tmp_path / "nas" / "GLM-processed" / "M1" / "10.0_20.0" /
                "1min" / "1900" / "01" / "01" / "00" /
                "OR_GLM-L2-GLMM1-M3_G16_s1900001000000*_e1900001000100*_c*.nc")


def test_find_coverage(glm_files, tmp_path, monkeypatch):
    """Test finding GLM time coverage."""
    from sattools.glm import find_glm_coverage
    monkeypatch.setenv("NAS_DATA", str(tmp_path / "nas"))
    covered = list(find_glm_coverage(
        datetime.datetime(1900, 1, 1, 0, 0, 0),
        datetime.datetime(1900, 1, 1, 0, 6, 0),
        sector="C"))
    pI = pandas.Interval
    pT = pandas.Timestamp

    assert covered == [
            pI(pT("1900-01-01T00:00:00"), pT("1900-01-01T00:01:00")),
            pI(pT("1900-01-01T00:01:00"), pT("1900-01-01T00:02:00")),
            pI(pT("1900-01-01T00:03:00"), pT("1900-01-01T00:04:00")),
            pI(pT("1900-01-01T00:05:00"), pT("1900-01-01T00:06:00"))]
    covered = list(find_glm_coverage(
        datetime.datetime(1900, 1, 2, 3, 4, 5),
        datetime.datetime(1900, 5, 4, 3, 2, 1),
        sector="C"))
    assert covered == []
    covered = list(find_glm_coverage(
        datetime.datetime(1900, 1, 1, 0, 0, 0),
        datetime.datetime(1900, 1, 1, 0, 6, 0),
        sector="F"))
    assert covered == [
            pI(pT("1900-01-01T00:00:00"), pT("1900-01-01T00:01:00")),
            pI(pT("1900-01-01T00:02:00"), pT("1900-01-01T00:03:00")),
            pI(pT("1900-01-01T00:05:00"), pT("1900-01-01T00:06:00"))]
    covered = list(find_glm_coverage(
        datetime.datetime(1900, 1, 1, 0, 0, 0),
        datetime.datetime(1900, 1, 1, 0, 9, 0),
        sector="M1", lat=1.2, lon=2.3))
    assert covered == [
            pI(pT("1900-01-01T00:00:00"), pT("1900-01-01T00:01:00")),
            pI(pT("1900-01-01T00:05:00"), pT("1900-01-01T00:06:00")),
            pI(pT("1900-01-01T00:08:00"), pT("1900-01-01T00:09:00"))]
    covered = list(find_glm_coverage(
        datetime.datetime(1900, 1, 1, 0, 0, 0),
        datetime.datetime(1900, 1, 1, 0, 9, 0),
        sector="M2", lat=1.2, lon=2.3))
    assert covered == [
            pI(pT("1900-01-01T00:00:00"), pT("1900-01-01T00:01:00")),
            pI(pT("1900-01-01T00:02:00"), pT("1900-01-01T00:03:00")),
            pI(pT("1900-01-01T00:04:00"), pT("1900-01-01T00:05:00"))]


def test_find_gaps(glm_files, monkeypatch, tmp_path):
    """Test finding GLM time coverage gaps."""
    from sattools.glm import find_glm_coverage_gaps
    monkeypatch.setenv("NAS_DATA", str(tmp_path / "nas"))
    pI = pandas.Interval
    pT = pandas.Timestamp
    gaps = list(find_glm_coverage_gaps(
        datetime.datetime(1900, 1, 1, 0, 0),
        datetime.datetime(1900, 1, 1, 0, 8),
        sector="C"))
    assert gaps == [
        pI(pT("1900-01-01T00:02:00"), pT("1900-01-01T00:03:00")),
        pI(pT("1900-01-01T00:04:00"), pT("1900-01-01T00:05:00")),
        pI(pT("1900-01-01T00:06:00"), pT("1900-01-01T00:08:00"))]
    gaps = list(find_glm_coverage_gaps(
        datetime.datetime(1900, 1, 2, 0, 0),
        datetime.datetime(1900, 1, 2, 0, 8),
        sector="C"))
    assert gaps == [
        pI(pT("1900-01-02T00:00:00"), pT("1900-01-02T00:08:00"))]
    gaps = list(find_glm_coverage_gaps(
        datetime.datetime(1900, 1, 1, 0, 0),
        datetime.datetime(1900, 1, 1, 0, 2),
        sector="C"))
    assert gaps == []
    gaps = list(find_glm_coverage_gaps(
        datetime.datetime(1900, 1, 1, 0, 0),
        datetime.datetime(1900, 1, 1, 0, 8),
        sector="F"))
    assert gaps == [
        pI(pT("1900-01-01T00:01:00"), pT("1900-01-01T00:02:00")),
        pI(pT("1900-01-01T00:03:00"), pT("1900-01-01T00:05:00")),
        pI(pT("1900-01-01T00:06:00"), pT("1900-01-01T00:08:00"))]
    gaps = list(find_glm_coverage_gaps(
        datetime.datetime(1900, 1, 1, 0, 0),
        datetime.datetime(1900, 1, 1, 0, 10),
        sector="M1", lat=1.2, lon=2.3))
    assert gaps == [
        pI(pT("1900-01-01T00:01:00"), pT("1900-01-01T00:05:00")),
        pI(pT("1900-01-01T00:06:00"), pT("1900-01-01T00:08:00")),
        pI(pT("1900-01-01T00:09:00"), pT("1900-01-01T00:10:00"))]
    gaps = list(find_glm_coverage_gaps(
        datetime.datetime(1900, 1, 1, 0, 0),
        datetime.datetime(1900, 1, 1, 0, 10),
        sector="M2", lat=1.2, lon=2.3))
    assert gaps == [
        pI(pT("1900-01-01T00:01:00"), pT("1900-01-01T00:02:00")),
        pI(pT("1900-01-01T00:03:00"), pT("1900-01-01T00:04:00")),
        pI(pT("1900-01-01T00:05:00"), pT("1900-01-01T00:10:00"))]


def test_run_glmtools(tmp_path, caplog, monkeypatch):
    """Test running glmtools."""
    from sattools.glm import run_glmtools
    monkeypatch.setenv("NAS_DATA", str(tmp_path / "nas"))
    with patch("sattools.glm.load_file") as sgl:
        mocks = [MagicMock() for _ in range(5)]
        sgl.return_value.grid_setup.return_value = mocks
        with caplog.at_level(logging.INFO):
            run_glmtools(
                    [tmp_path / "lcfa1.nc", tmp_path / "lcfa2.nc"],
                    sector="F")
            assert (f"Running glmtools for {(tmp_path / 'lcfa1.nc')!s}, "
                    f"{(tmp_path / 'lcfa2.nc')!s}" in caplog.text)
        mocks[0].assert_called_once()
        # confirm we passed the correct sector
        assert (cal := sgl().create_parser().parse_args.call_args_list
                [0][0][0])[
                cal.index("--goes_sector") + 1] == "full"
        # try with meso sector, requiring lat/lon
        run_glmtools(
                [tmp_path / "lcfa1.nc", tmp_path / "lcfa2.nc"],
                sector="M1", lat=45, lon=-120)
        assert (cal := sgl().create_parser().parse_args.call_args_list
                [-1][0][0])[
                cal.index("--goes_sector") + 1] == "meso"
        assert cal[cal.index("--ctr_lat") + 1] == "45.00"
        assert cal[cal.index("--ctr_lon") + 1] == "-120.00"
        # try with splitting
        mocks[0].reset_mock()
        run_glmtools([tmp_path / "lcfa1.nc", tmp_path / "lcfa2.nc"],
                     max_files=1)
        assert mocks[0].call_count == 2


@patch("importlib.util.spec_from_file_location", autospec=True)
@patch("importlib.util.module_from_spec", autospec=True)
def test_load_file(ium, ius):
    """Test loading file as module."""
    from sattools.glm import load_file
    load_file("module", "/dev/null")


def test_get_integrated_glm(tmp_path):
    """Test getting integrated GLM."""
    from sattools.glm import get_integrated_scene
    fake_glm = utils.create_fake_glm_for_period(
            tmp_path,
            datetime.datetime(1900, 1, 1, 0, 0, 0),
            datetime.datetime(1900, 1, 1, 0, 4, 0),
            "C")
    sc = get_integrated_scene(fake_glm)
    numpy.testing.assert_array_equal(
            sc["flash_extent_density"],
            numpy.full((10, 10), 5))
