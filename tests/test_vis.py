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


def test_flatten_areas():
    from sattools.area import flatten_areas
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
    flat = list(flatten_areas([*ars, sar, sar2]))
    assert all(isinstance(ar, pyresample.geometry.AreaDefinition)
               for ar in flat)
    assert len(flat) == 8
