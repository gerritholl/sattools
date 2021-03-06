"""Test tools related to reading ABI."""

import datetime
import pytest

import unittest.mock


@unittest.mock.patch("s3fs.S3FileSystem")
@pytest.mark.parametrize("sector", ["C", "F", "M1"])
def test_get_fs_and_files(sS, tmp_path, monkeypatch, sector):
    """Test getting FS and files."""
    from sattools.abi import get_fs_and_files
    from fsspec.implementations.local import LocalFileSystem
    from fsspec.implementations.cached import CachingFileSystem
    from typhon.files.handlers.common import FileInfo

    sS.side_effect = LocalFileSystem
    monkeypatch.chdir(tmp_path)
    for c in range(1, 4):
        tf = (tmp_path / "noaa-goes16" / f"ABI-L1b-Rad{sector[0]:s}" / "1900" /
              "001" / "00" / f"OR_ABI-L1b-Rad{sector:s}-M6C{c:>02d}_G16_"
              "s19000010005000_e19000010010000_c20303212359590.nc")
        tf.parent.mkdir(parents=True, exist_ok=True)
        tf.touch()

    (fs, fns) = get_fs_and_files(
            datetime.datetime(1900, 1, 1, 0),
            datetime.datetime(1900, 1, 1, 1),
            sector=sector,
            chans={2, 3})
    assert isinstance(fs, CachingFileSystem)
    assert len(fns) == 2
    assert fns == [
            FileInfo(
                path=str(tmp_path / "noaa-goes16" / f"ABI-L1b-Rad{sector[0]:s}"
                         / "1900" / "001" / "00" / f"OR_ABI-L1b-Rad{sector:s}-"
                         f"M6C{c:>02d}_G16_s19000010005000_e19000010010000_"
                         "c20303212359590.nc"),
                times=[datetime.datetime(1900, 1, 1, 0, 5),
                       datetime.datetime(1900, 1, 1, 0, 10)],
                attr={})
            for c in {2, 3}]

    (fs, fns) = get_fs_and_files(
            datetime.datetime(1900, 1, 1, 0),
            datetime.datetime(1900, 1, 1, 1),
            sector=sector,
            chans=12)
    assert fns == []


def test_split_meso(fake_multiscene4):
    """Test splitting MESO by area.
    """
    from sattools.abi import split_meso
    L = list(split_meso(fake_multiscene4))
    assert len(L) == 3
    assert len(L[0].scenes) == 6
    assert len(L[1].scenes) == 3
    assert len(L[2].scenes) == 1
    # assert that each dataset has the same area throughout the multiscene
    # (although areas between datasets can still differ)
    for did in fake_multiscene4.first_scene.keys():
        for ms in L:
            assert len({sc[did].attrs["area"] for sc in ms}) == 1
