"""Test visualisation routines."""

import datetime
import os

from unittest.mock import patch, MagicMock

import pandas
import pytest
import pyresample
import satpy.readers
import xarray
import numpy


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


def test_show_video_from_times(
        monkeypatch, tmp_path,
        better_glmc_pattern, more_glmc_files, fakearea):
    """Test showing an ABI/GLM video from times."""
    from sattools.vis import show_video_abi_glm_times
    from fsspec.implementations.local import LocalFileSystem

    def fake_ensure_glm(start_date, end_date, sector="C", lat=0, lon=0):
        iv = pandas.Timedelta(1, "min")
        files = []
        time_form = "%Y-%m-%dT%H:%M:%SZ"
        for dt in pandas.date_range(start_date, end_date, freq=iv):
            tf = (tmp_path / "GLM-processed" / sector / "1min" / f"{dt:%Y}" /
                  f"{dt:%m}" / f"{dt:%d}" / f"OR_GLM-L2-GLM{sector:s}-M3_G16_"
                  f"s{dt:%Y%j%H%M%S}0_e{dt+iv:%Y%j%H%M%S}0_c20403662359590.nc")
            tf.parent.mkdir(exist_ok=True, parents=True)
            ds = xarray.Dataset(
                    {"flash_extent_density": (("y", "x"), numpy.empty((10, 10))),
                     "goes_imager_projection": ((), 0, {
                        "longitude_of_projection_origin": -75.,
                        "latitude_of_projection_origin": 0.,
                        "perspective_point_height": 35786023.,
                        "semi_major_axis": 6378137.,
                        "semi_minor_axis": 6356752.31414,
                        "sweep_angle_axis": "x",
                        }),
                     "nominal_satellite_subpoint_lat": 0.,
                     "nominal_satellite_subpoint_lon": -75.,
                        },
                    attrs={
                        "time_coverage_start": dt.strftime(time_form),
                        "time_coverage_end": (dt+iv).strftime(time_form),
                        "spatial_resolution": "2km at nadir"})
            ds.to_netcdf(tf)
            files.append(os.fspath(tf))
        return files

    def fake_get_abi(start_date, end_date, sector, chans):
        lfs = LocalFileSystem()
        rep = {"M1": 1, "M2": 1, "C": 5, "F": 10}
        iv = pandas.Timedelta(rep[sector], "min")
        files = []
        time_form = "%Y-%m-%dT%H:%M:%S.%fZ"
        for dt in pandas.date_range(start_date, end_date, freq=iv):
            for chan in chans:
                tf = (tmp_path / "noaa-goes16" / f"ABI-L1b-Rad{sector:s}" /
                      f"{dt:%Y}" / f"{dt:%j}" / f"{dt:%H}" /
                      "001" / "00" /
                      f"OR_ABI-L1b-Rad{sector:s}-M6C{chan:d}_G16_"
                      f"s{dt:%Y%j%H%M%S0}_e{dt+iv/2:%Y%j%H%M%S0}_"
                      "c20403662359590.nc")
                tf.parent.mkdir(exist_ok=True, parents=True)
                ds = xarray.Dataset(
                        {"Rad": (("y", "x"), numpy.empty((10, 10))),
                         "planck_fk1": ((), 8510.22),
                         "planck_fk2": ((), 1286.27),
                         "planck_bc1": ((), 0.22516),
                         "planck_bc2": ((), 0.9992),
                         "nominal_satellite_subpoint_lat": ((), 0.),
                         "nominal_satellite_subpoint_lon": ((), -75.),
                         "nominal_satellite_height": ((), 35786.02),
                         "yaw_flip_flag": ((), 0),
                         "goes_imager_projection": ((), 0, {
                            "longitude_of_projection_origin": -75.,
                            "latitude_of_projection_origin": 0.,
                            "perspective_point_height": 35786023.,
                            "semi_major_axis": 6378137.,
                            "semi_minor_axis": 6356752.31414,
                            "sweep_angle_axis": "x"
                             })},
                        attrs={
                            "time_coverage_start": dt.strftime(time_form),
                            "time_coverage_end": (dt+iv).strftime(time_form)})
                ds.to_netcdf(tf)
                # Should test with FSFile here, but bug
                # https://github.com/pytroll/satpy/issues/1741 so testing with
                # just filename instead
                # should be: files.append(satpy.readers.FSFile(tf, fs=lfs))
                files.append(os.fspath(tf))
        return files

#    def fake_open(nc, decode_cf=True, mask_and_scale=False, chunks={}):
#        raise NotImplementedError()
#        ds = xarray.Dataset()
#        ds.attrs["time_coverage_start"] = "1900-01-01T00:00:00.0Z"
#        return ds

    monkeypatch.setenv("NAS_DATA", str(tmp_path / "nas"))
    with patch("sattools.abi.get_fsfiles", new=fake_get_abi), \
            patch("sattools.glm.ensure_glm_for_period", new=fake_ensure_glm):
#            patch("satpy.MultiScene") as sM:
        show_video_abi_glm_times(
            datetime.datetime(1900, 1, 1, 0, 0),
            datetime.datetime(1900, 1, 1, 0, 20),
            out_dir=tmp_path / "show-vid",
            vid_out="test.mp4",
            enh_args={})
    sM.from_files.return_value.save_animation.assert_called_once_with(
            os.fspath(tmp_path / "show-vid" / "test.mp4"),
            enh_args={})

#@pytest.mark.integtest
#def test_show_video_from_times_unmocked(tmp_path):
#    from sattools.vis import show_video_abi_glm_times
#    show_video_abi_glm_times(
#            datetime.datetime(2021, 6, 1, 18, 0),
#            datetime.datetime(2021, 6, 1, 18, 1),
#            out_dir=tmp_path / "show-vid",
#            vid_out="test.mp4",
#            enh_args={})
