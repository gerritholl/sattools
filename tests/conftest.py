# -*- coding: utf-8 -*-
"""conftest.py for sattools."""

import datetime
import copy
import pathlib

import pytest
import satpy
import satpy.tests.utils
import xarray
import numpy
import pyresample


@pytest.fixture(autouse=True)
def setUp(tmp_path, monkeypatch):
    """Set up environment variables for all tests."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "scratch"))


@pytest.fixture
def fakearea():
    """Make a 5x5 pixel area for full disc ABI."""
    from pyresample.geometry import AreaDefinition
    return AreaDefinition(
            "fribbulus xax", "fribbulus xax", "fribbulus xax",
            {'proj': 'geos', 'sweep': 'x', 'lon_0': -89.5, 'h': 35786023,
                'x_0': 0, 'y_0': 0, 'ellps': 'GRS80', 'units': 'm', 'no_defs':
                None, 'type': 'crs'},
            5, 5, (-5434894.8851, -4585692.5593, 4585692.5593, 5434894.8851))


@pytest.fixture
def fakescene(fakearea):
    """Return a fake scene with real areas."""
    # let's make a Scene
    #
    # should I mock get_xy_from_lonlat here?  Probably as it's an external
    # dependency that I can assume to be correct, and it simplifies the
    # unit test here.
    sc = satpy.Scene()
    for v in {"raspberry", "blueberry", "maroshki", "strawberry"}:
        sc[v] = xarray.DataArray(
                numpy.arange(25).reshape(5, 5),
                dims=("x", "y"),
                attrs={"area": fakearea})
    return sc


@pytest.fixture
def fake_multiscene():
    """Get a fake satpy MultiScene."""
    sc1 = satpy.tests.utils.make_fake_scene(
            {"rasberry": numpy.arange(5*5).reshape(5, 5),
             "straberry": numpy.arange(5*5).reshape(5, 5)})
    sc2 = satpy.tests.utils.make_fake_scene(
            {"rasberry": numpy.arange(6*6).reshape(6, 6),
             "straberry": numpy.arange(6*6).reshape(6, 6)})
    sc3 = satpy.tests.utils.make_fake_scene(
            {"rasberry": numpy.arange(5*5).reshape(5, 5),
             "straberry": numpy.arange(5*5).reshape(5, 5)},
            area=pyresample.geometry.StackedAreaDefinition(
                sc1["rasberry"].attrs["area"],
                sc2["rasberry"].attrs["area"]))
    sc2["no-area"] = xarray.DataArray(numpy.arange(5))
    return satpy.MultiScene([sc1, sc2, sc3])


@pytest.fixture
def fake_multiscene2():
    """Like fake_multiscene, but with real areas (one stacked)."""
    from satpy.dataset.dataid import WavelengthRange
    from satpy.tests.utils import make_dataid
    common_attrs = {
            "start_time": datetime.datetime(1900, 1, 1, 0, 0),
            "end_time": datetime.datetime(1900, 1, 1, 0, 1)}
    wl = {"C08": WavelengthRange(5.7, 6.2, 6.7),
          "C10": WavelengthRange(6.8, 7.3, 7.8),
          "C14": WavelengthRange(10, 11, 12)}
    content = {make_dataid(name=x, wavelength=wl.get(x)):
               numpy.arange(5*5).reshape(5, 5)
               for x in ("C08", "C10", "C14", "C14_flash_extent_density")}
    sc1 = satpy.tests.utils.make_fake_scene(
            content.copy(),
            common_attrs=common_attrs)
    sc2 = satpy.tests.utils.make_fake_scene(
            content.copy(),
            common_attrs=common_attrs)
    sc3 = satpy.tests.utils.make_fake_scene(
            {k: numpy.concatenate([v, v], 0) for (k, v) in content.items()},
            area=pyresample.geometry.StackedAreaDefinition(
                sc1["C14"].attrs["area"],
                sc2["C14"].attrs["area"]),
            common_attrs=common_attrs)
    return satpy.MultiScene([sc1, sc2, sc3])


@pytest.fixture
def fake_multiscene_empty():
    """Fake multiscene with empty scenes."""
    return satpy.MultiScene([satpy.Scene() for _ in range(3)])


@pytest.fixture
def fake_multiscene3(fake_multiscene2):
    """Like fake_multiscene2, but with real areas (none stacked)."""
    fms = satpy.MultiScene(copy.deepcopy(fake_multiscene2.scenes))
    for k in fms.scenes[2].keys():
        fms.scenes[2][k].attrs["area"] = fake_multiscene2.scenes[0][k].\
                attrs["area"]
    return fms


@pytest.fixture
def fake_multiscene_vary_meso():
    """Like fake_multiscene2, but with varying areas (none stacked)."""
    from satpy.dataset.dataid import WavelengthRange
    from satpy.tests.utils import make_dataid
    common_attrs = {}
    wl = {"C08": WavelengthRange(5.7, 6.2, 6.7),
          "C10": WavelengthRange(6.8, 7.3, 7.8),
          "C14": WavelengthRange(10, 11, 12)}
    content = {make_dataid(name=x, wavelength=wl.get(x)):
               numpy.arange(5*5).reshape(5, 5)
               for x in ("C08", "C10", "C14")}
    content[make_dataid(name="flash_extent_density")] = numpy.arange(
            5*5).reshape(5, 5)+1
    areas = [pyresample.create_area_def(
             "test-area",
             {"proj": "eqc", "lat_ts": 0, "lat_0": 0, "lon_0": 0,
              "x_0": 0, "y_0": 0, "ellps": "sphere", "units": "m",
              "no_defs": None, "type": "crs"},
             units="m",
             shape=(5, 5),
             resolution=1000,
             center=(10*i, 20*i)) for i in range(3)]

    aids = [0, 0, 0, 0, 0, 0, 1, 1, 1, 2]
    scenes = [satpy.tests.utils.make_fake_scene(
        content.copy(),
        common_attrs=common_attrs,
        area=areas[i]) for i in aids]
    for (i, sc) in enumerate(scenes):
        for da in sc.values():
            da.attrs["start_time"] = datetime.datetime(1900, 1, 1, 0, i)
            da.attrs["end_time"] = datetime.datetime(1900, 1, 1, 0, i+1)
    return satpy.MultiScene(scenes)


# @pytest.fixture
# def glmc_pattern(tmp_path):
#     # typhon fileset doesn't understand the full format-specification
#     # mini-language, so something like hour:>02d doesn't work...
#     return str(tmp_path / "nas" / "glmc-fake" /
#                "glmc-fake-{year}{month}{day}{hour}{minute}{second}-"
#                "{end_hour}{end_minute}{end_second}.nc")


@pytest.fixture
def better_glmc_pattern(tmp_path):
    """Return a GLMC pattern suitable for creation not just finding."""
    # typhon fileset doesn't understand the full format-specification
    # mini-language, so something like hour:>02d doesn't work...
    return str(tmp_path / "nas" / "GLM" / "GLMC" / "1min" / "{year}"
               / "{month}" / "{day}" / "{hour}" /
               "OR_GLM-L2-GLMC-M3_G16_s{year}{doy}{hour}{minute}{second}0_"
               "e{end_year}{end_doy}{end_hour}{end_minute}{end_second}0_"
               "c20403662359590.nc")


@pytest.fixture
def lcfa_pattern(tmp_path):
    """Fixture to mock pattern for LCFA files."""
    return str(tmp_path / "lcfa-fake" /
               "lcfa-fake-{year}{month}{day}{hour}{minute}{second}-"
               "{end_hour}{end_minute}{end_second}.nc")


def _mk_test_files(pattern, minutes):
    """Create test files in temporary directory."""
    pat = pathlib.Path(pattern)
    files = []
    for m in minutes:
        # ...(see line 11-12) therefore I need to pass strings here
        p = pathlib.Path(str(pat).format(
                    year="1900", month="01", day="01", hour="00",
                    minute=f"{m:>02d}", second="00",
                    end_year="1900", end_month="01", end_day="01",
                    end_hour="00", end_minute=f"{m+1:>02d}",
                    end_second="00", doy="001", end_doy="001"))
        p.parent.mkdir(exist_ok=True, parents=True)
        p.touch()
        files.append(p)
    return files


@pytest.fixture
def glm_files(monkeypatch, tmp_path):
    """Create GLM files and return the created ones."""
    from sattools.glm import get_pattern_dwd_glm
    monkeypatch.setenv("NAS_DATA", str(tmp_path / "nas"))
    glmc = _mk_test_files(
            get_pattern_dwd_glm("C"),
            (0, 1, 3, 5))
    glmf = _mk_test_files(
            get_pattern_dwd_glm("F"),
            (0, 2, 5))
    glmm1 = _mk_test_files(
            get_pattern_dwd_glm("M1", lat=1.2, lon=2.3),
            (0, 5, 8))
    glmm2 = _mk_test_files(
            get_pattern_dwd_glm("M2", lat=1.2, lon=2.3),
            (0, 2, 4))
    return glmc + glmf + glmm1 + glmm2


@pytest.fixture
def lcfa_files(lcfa_pattern):
    """Create LCFA files and return the created ones."""
    return _mk_test_files(lcfa_pattern, (0, 1, 2, 3, 4, 5))


@pytest.fixture
def more_glmc_files(better_glmc_pattern):
    """Create more GLMC files with a different pattern.

    Here the pattern is suitable for creation, not only for finding.
    """
    return _mk_test_files(better_glmc_pattern, range(30))
