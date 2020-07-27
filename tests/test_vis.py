"""Test visualisation routines
"""

import datetime
from unittest.mock import patch, MagicMock

import xarray
import numpy
import pytest
import satpy
import satpy.tests.utils
import pyresample


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


def test_show(fakescene, fakearea, tmp_path):
    import sattools.vis
    from satpy import Scene
    comps = ["raspberry", "blueberry"]
    chans = ["maroshki", "strawberry"]
    areas = ["native"]
    with patch("satpy.Scene") as sS:
        sS.return_value = fakescene
        S = sattools.vis.show(
                ["/tmp/animals/pinguin", "/tmp/animals/polarbear"],
                comps, chans, areas,
                tmp_path / "out", "{label:s}_{area:s}_{dataset:s}.tiff",
                reader="pranksat",
                label="fish")
    assert S == {tmp_path / "out" /
                 f"fish_{area:s}_{ds:s}.tiff"
                 for ds in ["raspberry", "blueberry", "maroshki", "strawberry"]
                 for area in ["native"]}
    for f in S:
        assert f.exists()
    fakescene.save_dataset = MagicMock()
    fakescene.resample = MagicMock()
    fakescene.resample.return_value = fakescene
    with patch("satpy.Scene") as sS:
        sS.return_value = fakescene
        S = sattools.vis.show(
                ["/tmp/animals/pinguin", "/tmp/animals/polarbear"],
                comps, chans, ["fribbulus xax"],
                tmp_path / "out", "{label:s}_{area:s}_{dataset:s}.tiff",
                reader="pranksat",
                show_only_coastlines="blueberry",
                path_to_coastlines="/coast", label="fish")
        S = sattools.vis.show(
                ["/tmp/animals/pinguin", "/tmp/animals/polarbear"],
                comps, chans, ["fribbulus xax"],
                tmp_path / "out", "{label:s}_{area:s}_{dataset:s}.tiff",
                reader="pranksat",
                show_only_coastlines=fakearea,
                path_to_coastlines="/coast", label="fish")
    assert S
    empty = Scene()
    with patch("satpy.Scene") as sS:
        sS.return_value = empty
        S = sattools.vis.show(
                ["/tmp/penguin"], [], [], ["home"],
                tmp_path / "not", "nowhere", reader="pranksat",
                show_only_coastlines=False, path_to_coastlines="/coast",
                label="bird")
    assert S == set()


@patch("satpy.MultiScene.from_files", autospec=True)
def test_show_video(sMf, fake_multiscene2, tmp_path):
    from sattools.vis import show_video_abi_glm
    sMf.return_value = fake_multiscene2
    mm = MagicMock()
    fake_multiscene2.resample = mm
    mm.return_value.scenes = fake_multiscene2.scenes[:1]*3
    for sc in fake_multiscene2.scenes:
        sc.save_datasets = MagicMock()
    show_video_abi_glm(
            ["fake_in1", "fake_in2"], tmp_path)
    mm.return_value.save_animation.assert_called_once()


def test_get_all_areas(fake_multiscene):
    from sattools.vis import _get_all_areas_from_multiscene
    areas = _get_all_areas_from_multiscene(fake_multiscene)
    assert len(areas) == 3


def test_flatten_areas():
    from sattools.vis import _flatten_areas
    ars = [pyresample.create_area_def(
            "test-area",
            {"proj": "eqc", "lat_ts": 0, "lat_0": 0, "lon_0": 0,
             "x_0": 0, "y_0": 0, "ellps": "sphere", "units": "m",
             "no_defs": None, "type": "crs"},
            units="m",
            shape=(r, r),
            resolution=1000,
            center=(0, 0)) for r in (5, 6)]
    sar = pyresample.geometry.StackedAreaDefinition(*ars)
    sar2 = pyresample.geometry.StackedAreaDefinition(sar, sar)
    flat = list(_flatten_areas([*ars, sar, sar2]))
    assert all(isinstance(ar, pyresample.geometry.AreaDefinition)
               for ar in flat)
    assert len(flat) == 8
