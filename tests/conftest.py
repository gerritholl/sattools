# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for sattools.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""

import datetime
import copy

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
    return satpy.MultiScene([sc1, sc2, sc3])


@pytest.fixture
def fake_multiscene2():
    """Like fake_multiscene1, but with real areas (one stacked).
    """
    common_attrs = {
            "start_time": datetime.datetime(1900, 1, 1, 0, 0),
            "end_time": datetime.datetime(1900, 1, 1, 0, 1)}
    sc1 = satpy.tests.utils.make_fake_scene(
            {"C14": numpy.arange(5*5).reshape(5, 5),
             "C14_flash_extent_density": numpy.arange(5*5).reshape(5, 5)},
            common_attrs=common_attrs)
    sc2 = satpy.tests.utils.make_fake_scene(
            {"C14": numpy.arange(5*5).reshape(5, 5),
             "C14_flash_extent_density": numpy.arange(5*5).reshape(5, 5)},
            common_attrs=common_attrs)
    sc3 = satpy.tests.utils.make_fake_scene(
            {"C14": numpy.arange(5*10).reshape(10, 5),
             "C14_flash_extent_density": numpy.arange(5*10).reshape(10, 5)},
            area=pyresample.geometry.StackedAreaDefinition(
                sc1["C14"].attrs["area"],
                sc2["C14"].attrs["area"]),
            common_attrs=common_attrs)
    return satpy.MultiScene([sc1, sc2, sc3])


@pytest.fixture
def fake_multiscene3(fake_multiscene2):
    """Like fake_multiscene2, but with real areas (none stacked).
    """
    fms = satpy.MultiScene(copy.deepcopy(fake_multiscene2.scenes))
    for k in fms.scenes[2].keys():
        fms.scenes[2][k].attrs["area"] = fake_multiscene2.scenes[0][k].\
                attrs["area"]
    return fms
