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


def test_plotdir(tmp_path, monkeypatch):
    from sattools.io import plotdir
    monkeypatch.delenv("PLOT_BASEDIR", raising=False)
    pd = plotdir(create=False)
    assert pd.parent.parent.parent == pathlib.Path(
            "/media/nas/x21308/plots_and_maps")
    pd = plotdir(create=False, basedir=tmp_path)
    assert pd.parent.parent.parent == tmp_path
    monkeypatch.setenv("PLOT_BASEDIR", str(tmp_path))
    pd = plotdir(create=False)
    assert pd.parent.parent.parent == tmp_path
    assert not pd.exists()
    pd = plotdir(create=True)
    assert pd.exists()


def test_datadir(tmp_path, monkeypatch):
    from sattools.io import datadir
    monkeypatch.delenv("NAS_DATA", raising=False)
    pd = datadir(create=False)
    assert pd == pathlib.Path("/media/nas/x21308/data")
    monkeypatch.setenv("NAS_DATA", tmp_path)
    pd = datadir(create=False)
    assert pd == tmp_path / "data"
    assert not pd.exists()
    pd = datadir(create=True)
    assert pd.exists()
    pd = datadir(tmp_path / "fionnay", subdir="datum", create=True)
    assert pd == tmp_path / "fionnay" / "datum"
    assert pd.exists()
