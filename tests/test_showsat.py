"""Test the showsat script."""

from unittest.mock import patch


@patch("argparse.ArgumentParser", autospec=True)
def test_get_parser(ap):
    """Test getting argument parser."""
    import sattools.processing.showsat
    sattools.processing.showsat.parse_cmdline()
    assert ap.return_value.add_argument.call_count == 9


@patch("satpy.Scene", autospec=True)
@patch("sattools.processing.showsat.parse_cmdline", autospec=True)
def test_main(fpsp, sS, tmp_path):
    """Test main function."""
    import sattools.processing.showsat
    fpsp.return_value = sattools.processing.showsat.\
        get_parser().parse_args([
                str(tmp_path / "out"),
                str(tmp_path / "in1"),
                str(tmp_path / "in2"),
                str(tmp_path / "in3"),
                "--composites", "overview", "natural_color", "fog",
                "--channels", "vis_04", "nir_13", "ir_38", "wv_87",
                "-a", "socotra", "bornholm", "-r", "fci_l1c_fdhsi"])

    sattools.processing.showsat.main()
    sS.assert_called_once_with(
            filenames=[str(tmp_path / f"in{i:d}") for i in (1, 2, 3)],
            reader="fci_l1c_fdhsi")
