"""Test the showsat script
"""

import unittest.mock


@unittest.mock.patch("argparse.ArgumentParser", autospec=True)
def test_get_parser(ap):
    import sattools.processing.video
    sattools.processing.video.parse_cmdline()
    assert ap.return_value.add_argument.call_count == 5


@unittest.mock.patch("satpy.MultiScene.from_files", autospec=True)
@unittest.mock.patch("sattools.processing.video.parse_cmdline", autospec=True)
def test_main(fpvp, sMf, fake_multiscene2, fake_multiscene3, tmp_path):
    import sattools.processing.video
    fpvp.return_value = sattools.processing.video.\
        get_parser().parse_args([
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

    sattools.processing.video.main()
    sMf.assert_called_once_with(
            [tmp_path / f"in{i:d}" for i in (1, 2, 3)],
            reader=["glm_l2", "abi_l1b"],
            ensure_all_readers=True,
            group_keys=["start_time"],
            time_threshold=35)
    assert (tmp_path / "out_dir" / "test-C14.tiff").exists()
