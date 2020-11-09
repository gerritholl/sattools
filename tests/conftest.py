# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for sattools.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""

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
    """Like fake_multiscene1, but with real areas (one stacked).
    """
    common_attrs = {
            "start_time": datetime.datetime(1900, 1, 1, 0, 0),
            "end_time": datetime.datetime(1900, 1, 1, 0, 1)}
    content = {x: numpy.arange(5*5).reshape(5, 5)
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
    """Fake multiscene with empty scenes.
    """

    return satpy.MultiScene([satpy.Scene() for _ in range(3)])


@pytest.fixture
def fake_multiscene3(fake_multiscene2):
    """Like fake_multiscene2, but with real areas (none stacked).
    """
    fms = satpy.MultiScene(copy.deepcopy(fake_multiscene2.scenes))
    for k in fms.scenes[2].keys():
        fms.scenes[2][k].attrs["area"] = fake_multiscene2.scenes[0][k].\
                attrs["area"]
    return fms


@pytest.fixture
def glmc_pattern(tmp_path):
    # typhon fileset doesn't understand the full format-specification
    # mini-language, so something like hour:>02d doesn't work...
    return str(tmp_path / "glmc-fake" /
               "glmc-fake-{year}{month}{day}{hour}{minute}{second}-"
               "{end_hour}{end_minute}{end_second}.nc")


@pytest.fixture
def better_glmc_pattern(tmp_path):
    # typhon fileset doesn't understand the full format-specification
    # mini-language, so something like hour:>02d doesn't work...
    return str(tmp_path / "noaa-goes16" / "GLM-L2-GLMC" / "{year}" / "{doy}"
               / "{hour}" /
               "OR_GLM-L2-GLMC-M3_G16_s{year}{doy}{hour}{minute}{second}0_"
               "e{end_year}{end_doy}{end_hour}{end_minute}{end_second}0_"
               "c20403662359590.nc")


@pytest.fixture
def lcfa_pattern(tmp_path):
    return str(tmp_path / "lcfa-fake" /
               "lcfa-fake-{year}{month}{day}{hour}{minute}{second}-"
               "{end_hour}{end_minute}{end_second}.nc")


def _mk_test_files(pattern, minutes):
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
def glmc_files(glmc_pattern):
    return _mk_test_files(glmc_pattern, (0, 1, 3, 5))


@pytest.fixture
def lcfa_files(lcfa_pattern):
    return _mk_test_files(lcfa_pattern, (0, 1, 2, 3, 4, 5))


@pytest.fixture
def more_glmc_files(better_glmc_pattern):
    return _mk_test_files(better_glmc_pattern, range(30))
