"""Test visualisation routines."""

import datetime

from unittest.mock import patch, MagicMock, ANY

import pytest
import pyresample


def test_show(fakescene, fakearea, tmp_path):
    """Test showing a scene and area."""
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
def test_show_video(sMf, fake_multiscene2, fake_multiscene3, tmp_path):
    """Test showing an ABI/GLM video from files."""
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
    sMf.return_value = fake_multiscene3
    fake_multiscene3.resample = MagicMock()
    fake_multiscene3.resample.return_value = fake_multiscene3
    with pytest.raises(ValueError):
        show_video_abi_glm(
                ["fake_in1", "fake_in2"], tmp_path)


def test_flatten_areas():
    """Test flattening a stacked area definition."""
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


@patch("s3fs.S3FileSystem")
@patch("subprocess.run")
@patch("satpy.multiscene.Scene")
@patch("sattools.vis.show_video_abi_glm")
@pytest.mark.xfail
def test_show_video_from_times(
        svs, smS, sr, sS, monkeypatch, tmp_path,
        better_glmc_pattern, more_glmc_files, fakearea):
    """Test showing an ABI/GLM video from times."""
    from sattools.vis import show_video_abi_glm_times
    from fsspec.implementations.local import LocalFileSystem
    from fsspec.implementations.cached import CachingFileSystem
    sS.return_value = LocalFileSystem()

    monkeypatch.chdir(tmp_path)
    for i in range(3):
        for s in ("M1", "M2"):
            tf = (tmp_path / "noaa-goes16" / f"ABI-L1b-Rad{s:s}" / "1900" /
                  "001" / "00" / f"OR_ABI-L1b-Rad{s:s}-M6C14_G16_"
                  f"s19000010{i:>02d}0000_e19000010{i+1:>02d}0000_"
                  "c20403662359590.nc")
            tf.parent.mkdir(exist_ok=True, parents=True)
            tf.touch()

    smS.return_value.__getitem__.return_value.attrs.\
        __getitem__.return_value = fakearea
    monkeypatch.setenv("NAS_DATA", str(tmp_path / "nas"))
    show_video_abi_glm_times(
            datetime.datetime(1900, 1, 1, 0, 0),
            datetime.datetime(1900, 1, 1, 0, 20),
            out_dir=tmp_path / "show-vid")
    exp_args = [
            str(tmp_path / "nas" / "GLM" / "GLMC" / "1min" / "1900" / "01" /
                "01" / "00" / f"OR_GLM-L2-GLMC-M3_G16_s190000100{i:>02d}000_"
                f"e190000100{i+1:>02d}000_c20403662359590.nc")
            for i in range(20)] + [
            str(tmp_path / "noaa-goes16" / f"ABI-L1b-RadM{j:d}" / "1900" /
                "001" / "00" / f"OR_ABI-L1b-RadM{j:d}-M6C14_G16_"
                f"s190000100{i:>01d}0000_"
                f"e190000100{i+1:>01d}0000_c20403662359590.nc")
            for i in range(2) for j in range(1, 3)]
    svs.assert_called_once_with(exp_args, tmp_path/"show-vid",
                                scene_kwargs=ANY)

    assert isinstance(
        svs.call_args[1]["scene_kwargs"]["reader_kwargs"]["glm_l2"]
                        ["file_system"],
        LocalFileSystem)
    assert isinstance(
        svs.call_args[1]["scene_kwargs"]["reader_kwargs"]["abi_l1b"]
                        ["file_system"],
        CachingFileSystem)
