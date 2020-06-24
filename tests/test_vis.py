"""Test visualisation routines
"""

import datetime
import pathlib
from unittest.mock import patch, call, MagicMock

import xarray
import numpy
import pytest
import satpy

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
    st_tm = datetime.datetime(1899, 12, 31, 23, 55)
    sc = satpy.Scene()
    for v in {"raspberry", "blueberry", "maroshki", "strawberry"}:
        sc[v] = xarray.DataArray(
                numpy.arange(25).reshape(5, 5),
                dims=("x", "y"),
                attrs={"area": fakearea})
    return sc


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
        S = sattools.vis.show(["/tmp/penguin"], [], [], ["home"],
                tmp_path / "not", "nowhere", reader="pranksat",
                show_only_coastlines=False, path_to_coastlines="/coast",
                label="bird")
    assert S == set()
