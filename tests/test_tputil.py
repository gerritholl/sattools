"""Test routines interacting with typhon."""


def test_fileinfo2fspath():
    """Test converting fileinfo to fspath object."""
    from typhon.files.handlers.common import FileInfo
    from satpy.readers import FSFile
    from sattools.tputil import fileinfo2fspath
    from fsspec.implementations.local import LocalFileSystem

    lfs = LocalFileSystem()
    fi = FileInfo("/tmp/tofu", fs=lfs)
    fsf = FSFile("/tmp/tofu", fs=lfs)
    assert fileinfo2fspath(fi) == fsf
    assert isinstance(fsf._file, str)
