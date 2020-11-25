import datetime
import unittest.mock

import satpy
import pytest


def test_get_all_areas(fake_multiscene):
    from sattools.scutil import _get_all_areas_from_multiscene
    areas = _get_all_areas_from_multiscene(fake_multiscene)
    assert len(areas) == 3


@unittest.mock.patch("satpy.MultiScene.from_files", autospec=True)
def test_get_resampled_multiscene(
        sMf, tmp_path, fake_multiscene_empty, fake_multiscene2):
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
@unittest.mock.patch("sattools.abi.get_fs_and_files", autospec=True)
def test_prepare_args(sag, sge, tmp_path):
    from sattools.scutil import prepare_abi_glm_ms_args
    from fsspec.implementations.local import LocalFileSystem
    from typhon.files.handlers.common import FileInfo
    sge.return_value = [
            FileInfo(path=str(tmp_path / f"glm{i:d}"),
                     times=[datetime.datetime(1900, 1, 1, 0, i),
                            datetime.datetime(1900, 1, 1, 0, i+1)],
                     attr={})
            for i in range(5)]
    sag.return_value = (
            LocalFileSystem(),
            [FileInfo(path=str(tmp_path / f"abi{i:d}"),
                      times=[datetime.datetime(1900, 1, 1, 0, i),
                             datetime.datetime(1900, 1, 1, 0, i+1)],
                      attr={})
             for i in range(5)])
    (gfs, gf, afs, af, kw) = prepare_abi_glm_ms_args(
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


@unittest.mock.patch("sattools.glm.ensure_glm_for_period", autospec=True)
@unittest.mock.patch("sattools.abi.get_fs_and_files", autospec=True)
def test_get_multiscenes(sag, sge, fake_multiscene4, tmp_path):
    from sattools.scutil import get_abi_glm_multiscenes
    from sattools.abi import split_meso
    from fsspec.implementations.local import LocalFileSystem
    from typhon.files.handlers.common import FileInfo

    sge.return_value = [
            FileInfo(path=str(tmp_path / f"glm{i:d}"),
                     times=[datetime.datetime(1900, 1, 1, 0, i),
                            datetime.datetime(1900, 1, 1, 0, i+1)],
                     attr={})
            for i in range(5)]
    sag.return_value = (
            LocalFileSystem(),
            [FileInfo(path=str(tmp_path / f"abi{i:d}"),
                      times=[datetime.datetime(1900, 1, 1, 0, i),
                             datetime.datetime(1900, 1, 1, 0, i+1)],
                      attr={})
             for i in range(5)])

    others = list(split_meso(fake_multiscene4))

    class FakeMultiScene(satpy.MultiScene):
        @classmethod
        def from_files(cls, files_to_sort, reader=None,
                       ensure_all_readers=False, scene_kwargs=None,
                       **kwargs):
            if reader == ["abi_l1b"]:
                return fake_multiscene4
            else:
                return others[0]

    with unittest.mock.patch("satpy.MultiScene", new=FakeMultiScene):
        mss = list(get_abi_glm_multiscenes(
                datetime.datetime(1900, 1, 1, 0, 0),
                datetime.datetime(1900, 1, 1, 1, 0),
                chans=[8, 10],
                sector="M1"))
        assert "C08" in mss[0].first_scene
        assert "C10" in mss[0].first_scene
        assert "flash_extent_density" in mss[0].first_scene
        # should be requesting GLM for the first six minutes, sector M1,
        # lat/lon centred at 0
        sge.assert_any_call(
                datetime.datetime(1900, 1, 1, 0, 0),
                datetime.datetime(1900, 1, 1, 0, 6),
                sector="M1",
                lat=0.0,
                lon=0.0)
        with pytest.raises(NotImplementedError):
            mss = list(get_abi_glm_multiscenes(
                    datetime.datetime(1900, 1, 1, 0, 0),
                    datetime.datetime(1900, 1, 1, 1, 0),
                    chans=[8, 10],
                    sector="F"))
        with pytest.raises(ValueError):
            mss = list(get_abi_glm_multiscenes(
                    datetime.datetime(1900, 1, 1, 0, 0),
                    datetime.datetime(1900, 1, 1, 1, 0),
                    chans=[8, 10],
                    sector="full"))
        assert list(get_abi_glm_multiscenes(
                datetime.datetime(1900, 1, 1, 0, 0),
                datetime.datetime(1900, 1, 1, 1, 0),
                chans=[8, 10],
                sector="M1",
                limit=0)) == []
