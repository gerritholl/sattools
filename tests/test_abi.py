"""Test tools related to reading ABI."""

import datetime
import pytest

import unittest.mock


@unittest.mock.patch("s3fs.S3FileSystem")
@pytest.mark.parametrize("sector", ["C", "F"])
def test_get_fs_and_files(sS, tmp_path, monkeypatch, sector):
    """Test getting FS and files."""
    from sattools.abi import get_fs_and_files
    from fsspec.implementations.local import LocalFileSystem
    from fsspec.implementations.cached import CachingFileSystem
    from typhon.files.handlers.common import FileInfo

    sS.side_effect = LocalFileSystem
    monkeypatch.chdir(tmp_path)
    tf = (tmp_path / "noaa-goes16" / f"ABI-L1b-Rad{sector:s}" / "1900" /
          "001" / "00" / f"OR_ABI-L1b-Rad{sector:s}-M6C1_G16_"
          "s19000010005000_e19000010010000_c20303212359590.nc")
    tf.parent.mkdir(parents=True)
    tf.touch()

    (fs, fns) = get_fs_and_files(
            datetime.datetime(1900, 1, 1, 0),
            datetime.datetime(1900, 1, 1, 1),
            sector=sector)
    assert isinstance(fs, CachingFileSystem)
    assert fns == [
            FileInfo(
                path=str(tmp_path / "noaa-goes16" / f"ABI-L1b-Rad{sector:s}"
                         / "1900" / "001" / "00" / f"OR_ABI-L1b-Rad{sector:s}-"
                         "M6C1_G16_s19000010005000_e19000010010000_"
                         "c20303212359590.nc"),
                times=[datetime.datetime(1900, 1, 1, 0, 5),
                       datetime.datetime(1900, 1, 1, 0, 10)],
                attr={})]
