"""Test the showsat script."""

import datetime
import unittest.mock

import pandas


@unittest.mock.patch("argparse.ArgumentParser", autospec=True)
def test_get_parser(ap):
    """Test argument parser."""
    from sattools.processing.video import (parse_cmdline, get_parser_files,
                                           get_parser_times)
    parse_cmdline(get_parser_files)
    assert ap.return_value.add_argument.call_count == 5
    ap.reset_mock()
    parse_cmdline(get_parser_times)
    assert ap.return_value.add_argument.call_count == 8


@unittest.mock.patch("satpy.MultiScene.from_files", autospec=True)
@unittest.mock.patch("sattools.processing.video.parse_cmdline", autospec=True)
def test_video_files(fpvp, sMf, fake_multiscene2, fake_multiscene3, tmp_path):
    """Test that files from video are called correctly."""
    import sattools.processing.video
    fpvp.return_value = sattools.processing.video.\
        get_parser_files().parse_args([
                str(tmp_path / "out_dir"),
                str(tmp_path / "in1"),
                str(tmp_path / "in2"),
                str(tmp_path / "in3"),
                "--filename-pattern-image", "test-{name:s}.tiff",
                "--filename-pattern-video", "test-{name:s}.mp4",
                "--coastline-dir", str(tmp_path / "coast_dir")])
    sMf.return_value = fake_multiscene2
    fake_multiscene2.resample = unittest.mock.MagicMock()
    fake_multiscene2.resample.return_value = fake_multiscene3
    fake_multiscene3.save_animation = unittest.mock.MagicMock()
    fake_multiscene3.scenes[2].save_datasets = unittest.mock.MagicMock()

    sattools.processing.video.video_files()
    sMf.assert_called_once_with(
            [str(tmp_path / f"in{i:d}") for i in (1, 2, 3)],
            reader=["glm_l2", "abi_l1b"],
            ensure_all_readers=True,
            group_keys=["start_time"],
            scene_kwargs={},
            time_threshold=35)
    fake_multiscene3.save_animation.assert_called_once()
    fake_multiscene3.scenes[2].save_datasets.assert_called_once()
    assert not (tmp_path / "out_dir" / "test-C14.tiff").exists()


@unittest.mock.patch("sattools.vis.show_video_abi_glm_times", autospec=True)
@unittest.mock.patch("sattools.processing.video.parse_cmdline", autospec=True)
def test_video_times(spvp, svs, tmp_path):
    """Test creating video with times."""
    from sattools.processing import video
    spvp.return_value = video.get_parser_times().parse_args([
        "1900-01-01T12:00:00", "1900-01-01T12:30:00",
        "--area", "panama", "--sector", "F", "--outdir",
        str(tmp_path / "out"),
        "--filename-pattern-image", "img.tif",
        "--filename-pattern-video", "video.mp4"])
    video.video_times()
    svs.assert_called_once_with(
            start_date=pandas.Timestamp(datetime.datetime(1900, 1, 1, 12, 0)),
            end_date=pandas.Timestamp(datetime.datetime(1900, 1, 1, 12, 30)),
            img_out="img.tif",
            vid_out="video.mp4",
            area="panama",
            sector="F",
            out_dir=tmp_path / "out")
