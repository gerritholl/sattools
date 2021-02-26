"""Test tools related to reading ABI."""

import datetime
import pytest

import unittest.mock


@unittest.mock.patch("s3fs.S3FileSystem")
@pytest.mark.parametrize("sector", ["C", "F", "M1"])
def test_get_fs_and_files(sS, tmp_path, monkeypatch, sector):
    """Test getting FSFile objects."""
    from sattools.abi import get_fsfiles
    from fsspec.implementations.local import LocalFileSystem
    from satpy.readers import FSFile

    sS.side_effect = LocalFileSystem
    monkeypatch.chdir(tmp_path)
    for c in range(1, 4):
        tf = (tmp_path / "noaa-goes16" / f"ABI-L1b-Rad{sector[0]:s}" / "1900" /
              "001" / "00" / f"OR_ABI-L1b-Rad{sector:s}-M6C{c:>02d}_G16_"
              "s19000010005000_e19000010010000_c20303212359590.nc")
        tf.parent.mkdir(parents=True, exist_ok=True)
        tf.touch()

    fsfs = get_fsfiles(
            datetime.datetime(1900, 1, 1, 0),
            datetime.datetime(1900, 1, 1, 1),
            sector=sector,
            chans={2, 3})
    assert isinstance(fsfs[0], FSFile)
    assert len(fsfs) == 2
    assert [str(fsf) for fsf in fsfs] == [
                str(tmp_path / "noaa-goes16" / f"ABI-L1b-Rad{sector[0]:s}"
                    / "1900" / "001" / "00" / f"OR_ABI-L1b-Rad{sector:s}-"
                    f"M6C{c:>02d}_G16_s19000010005000_e19000010010000_"
                    "c20303212359590.nc")
                for c in {2, 3}]

    assert get_fsfiles(
            datetime.datetime(1900, 1, 1, 0),
            datetime.datetime(1900, 1, 1, 1),
            sector=sector,
            chans=12) == []


def test_split_meso(fake_multiscene4):
    """Test splitting MESO by area."""
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
