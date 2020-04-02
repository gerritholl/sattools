import tempfile
import os
import pathlib


def test_cache_dir():
    from sattools.io import get_cache_dir
    with tempfile.TemporaryDirectory() as tmpdir:
        d = get_cache_dir(tmpdir, "tofu")
        assert str(d.parent) == tmpdir
        assert d.name == "tofu"
    try:
        _environ = os.environ.copy()
        os.environ.pop("XDG_CACHE_HOME", None)
        d = get_cache_dir(subdir="raspberry")
        assert d.parent.name == ".cache"
        assert d.name == "raspberry"
    finally:
        try:
            d.rmdir()
        except OSError:
            pass
        os.environ.clear()
        os.environ.update(_environ)
    try:
        _environ = os.environ.copy()
        pt = pathlib.Path(os.environ.get("TMPDIR", "/tmp/"))
        os.environ["XDG_CACHE_HOME"] = str(pt)
        d = get_cache_dir(subdir="banana")
        assert d.parent == pt
        assert d.name == "banana"
    finally:
        try:
            d.rmdir()
        except OSError:
            pass
        os.environ.clear()
        os.environ.update(_environ)
