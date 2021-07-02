"""Tests related to scutil module."""
import datetime
import unittest.mock

import numpy

import satpy
import pyresample.geometry
import pytest
from . import utils


def test_get_all_areas(fake_multiscene):
    """Test getting areas from multiscene."""
    from sattools.scutil import _get_all_areas_from_multiscene
    areas = _get_all_areas_from_multiscene(fake_multiscene)
    assert len(areas) == 3


@unittest.mock.patch("satpy.MultiScene.from_files", autospec=True)
def test_get_resampled_multiscene(
        sMf, tmp_path, fake_multiscene_empty, fake_multiscene2):
    """Test getting a resampled multiscene from files."""
    from sattools.scutil import get_resampled_multiscene
    sMf.return_value = fake_multiscene_empty

    def load(ds_all, unload=None):
        for (sc, ref_sc) in zip(
                fake_multiscene_empty.scenes, fake_multiscene2.scenes):
            for ds in ds_all:
                sc[ds] = ref_sc[ds]

    fake_multiscene_empty.load = load
    ms = get_resampled_multiscene(
            [str(tmp_path / f"in{i:d}") for i in (1, 2, 3)],
            ["glm", "abi"],
            "C14",
            ["C14_flash_extent_density"])
    assert ms[0] is fake_multiscene_empty
    assert "C14" in ms[0].first_scene
    assert "C10" not in ms[0].first_scene
    sMf.assert_called_once_with(
            [str(tmp_path / f"in{i:d}") for i in (1, 2, 3)],
            reader=["glm", "abi"],
            ensure_all_readers=True,
            scene_kwargs={},
            group_keys=["start_time"],
            time_threshold=35)
    ms = get_resampled_multiscene(
            [str(tmp_path / f"in{i:d}") for i in (1, 2, 3)],
            ["glm", "abi"],
            "C08",
            ["C10"])
    assert "C10" in ms[0].first_scene
    ms = get_resampled_multiscene(
            [str(tmp_path / f"in{i:d}") for i in (1, 2, 3)],
            ["glm", "abi"],
            6.2,
            [7.3])
    assert "C10" in ms[0].first_scene


@unittest.mock.patch("sattools.glm.ensure_glm_for_period", autospec=True)
@unittest.mock.patch("sattools.abi.get_fsfiles", autospec=True)
def test_prepare_args(sag, sge, tmp_path):
    """Test preparing arguments for getting ABI and GLM data."""
    from sattools.scutil import prepare_abi_glm_ms_args
    from fsspec.implementations.local import LocalFileSystem
    from typhon.files.handlers.common import FileInfo
    from satpy.readers import FSFile
    sge.return_value = [
            FileInfo(path=str(tmp_path / f"glm{i:d}"),
                     times=[datetime.datetime(1900, 1, 1, 0, i),
                            datetime.datetime(1900, 1, 1, 0, i+1)],
                     attr={})
            for i in range(5)]
    sag.return_value = [
            FSFile(tmp_path / f"abi{i:d}", LocalFileSystem())
            for i in range(5)]
    (gfsfs, afsfs) = prepare_abi_glm_ms_args(
            datetime.datetime(1900, 1, 1, 0),
            datetime.datetime(1900, 1, 1, 6),
            chans={8, 10},
            sector="F")
    assert sag.call_args[1]["sector"] == "F"
    assert sge.call_args[1]["sector"] == "F"
    with pytest.raises(ValueError):
        prepare_abi_glm_ms_args(
            datetime.datetime(1900, 1, 1, 0),
            datetime.datetime(1900, 1, 1, 6),
            chans={8, 10},
            sector="M1")


def test_get_multiscenes(tmp_path):
    """Test getting a multiscene with ABI and GLM."""
    from sattools.scutil import get_abi_glm_multiscenes

    def fake_ensure_glm(start, end, sector=None, lon=None, lat=None):
        return utils.create_fake_glm_for_period(
                tmp_path, start, end, sector)

    def fake_abi_getfsfiles(start, end, sector=None, chans=None):
        return utils.create_fake_abi_for_period(
                tmp_path, start, end, sector=sector, chans=chans)
    # test meso situation

    with unittest.mock.patch("sattools.glm.ensure_glm_for_period",
                             new=fake_ensure_glm), \
         unittest.mock.patch("sattools.abi.get_fsfiles",
                             new=fake_abi_getfsfiles):
        mss = list(get_abi_glm_multiscenes(
                datetime.datetime(1900, 1, 1, 0, 0),
                datetime.datetime(1900, 1, 1, 0, 10),
                chans=[8, 10],
                sector="M1"))
        assert "C08" in mss[0].first_scene
        assert "C10" in mss[0].first_scene
        assert "flash_extent_density" in mss[0].first_scene

        assert list(get_abi_glm_multiscenes(
                datetime.datetime(1900, 1, 1, 0, 0),
                datetime.datetime(1900, 1, 1, 0, 10),
                chans=[8, 10],
                sector="M1",
                limit=0)) == []

    # test full situation

    #    with unittest.mock.patch("satpy.MultiScene") as sM:
        mss = list(get_abi_glm_multiscenes(
                datetime.datetime(1900, 1, 1, 0, 0),
                datetime.datetime(1900, 1, 1, 1, 0),
                chans=[8, 10],
                sector="F"))
        assert len(mss) == 1
    #    assert sM.from_files.call_count == 1
        with pytest.raises(ValueError):
            mss = list(get_abi_glm_multiscenes(
                    datetime.datetime(1900, 1, 1, 0, 0),
                    datetime.datetime(1900, 1, 1, 1, 0),
                    chans=[8, 10],
                    sector="full"))


def test_collapse_multiscene():
    """Test collapsing a multiscene."""
    from sattools.scutil import collapse_abi_glm_multiscene
    cont_part = {"flash_extent_density": numpy.arange(6*6).reshape(6, 6)}
    cont_full = cont_part.copy()
    cont_full["strawberry"] = numpy.arange(6*6).reshape(6, 6)
    in_ = satpy.MultiScene(
        [satpy.tests.utils.make_fake_scene(
            cont_full if i % 3 == 0 else cont_part)
            for i in range(6)])
    for sc in in_.scenes:
        sc["flash_extent_density"].attrs["sensor"] = "glm"
        if "strawberry" in sc:
            sc["strawberry"].attrs["sensor"] = "abi"
    ref = satpy.MultiScene(
            [satpy.tests.utils.make_fake_scene(
                {"flash_extent_density": cont_part["flash_extent_density"],
                 "strawberry": 3*cont_full["strawberry"]})
                for i in range(2)])
    out = collapse_abi_glm_multiscene(in_)
    # cannot directly compare multiscene or scene, see
    # https://github.com/pytroll/satpy/issues/1583
    assert len(out.scenes) == len(ref.scenes)
    for (outscene, refscene) in zip(out.scenes, ref.scenes):
        assert (outscene.to_xarray_dataset() ==
                refscene.to_xarray_dataset()).all()


def test_get_collapsed_multiscene_from_groups(tmp_path):
    """Test getting a collapsed multiscene from groups."""
    from sattools.scutil import get_collapsed_multiscene_from_groups
    fake_glm = utils.create_fake_glm_for_period(
            tmp_path,
            datetime.datetime(1900, 1, 1, 0, 0, 0),
            datetime.datetime(1900, 1, 1, 0, 9, 0),
            "C")
    fake_abi = utils.create_fake_abi_for_period(
            tmp_path,
            datetime.datetime(1900, 1, 1, 0, 0, 0),
            datetime.datetime(1900, 1, 1, 0, 5, 0),
            "C",
            [14])
    assert len(fake_glm) == 10
    assert len(fake_abi) == 2
    groups = [
            {"abi_l1b": fake_abi[0:1], "glm_l2": fake_glm[0:5]},
            {"abi_l1b": fake_abi[1:2], "glm_l2": fake_glm[5:10]},
            ]
    ms = get_collapsed_multiscene_from_groups(
            groups, ["C14", "C14_flash_extent_density",
                     "flash_extent_density"])
    assert len(ms.scenes) == 2
    for sc in ms.scenes:
        assert {x["name"] for x in sc.keys()} == {
                "flash_extent_density", "C14", "C14_flash_extent_density"}
        for k in sc.keys():
            assert isinstance(sc[k].attrs["area"],
                              pyresample.geometry.AreaDefinition)
        numpy.testing.assert_array_equal(
                sc["flash_extent_density"].data,
                numpy.full((10, 10), 5))
        numpy.testing.assert_array_almost_equal(
                sc["C14"].data,
                numpy.full((10, 10), 142.031245))
