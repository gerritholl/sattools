import datetime
import logging
import unittest.mock


def test_setup_handler(tmp_path):
    import sattools.log
    sattools.log.setup_main_handler(
            ["banana"], filename=tmp_path / "test.log")
    logger = logging.getLogger("banana")
    assert len(logger.handlers) == 2


def test_log_context(tmp_path):
    import sattools.log
    tofu = logging.getLogger("tofu")
    veggie = logging.getLogger("veggie")
    # substitute for stderr on other handler
    oh = logging.FileHandler(tmp_path / "oh")
    tofu.addHandler(oh)
    with sattools.log.LogToTimeFile(tmp_path / "ah") as c:
        # I want everything to be logged to the file
        f = c.logfile
        tofu.debug("tofu")
        veggie.debug("veggie")
    with f.open("r") as fp:
        text = fp.read()
        assert "tofu" in text
        assert "veggie" in text
    # I want none of this to appear on stderr
    with (tmp_path / "oh").open("r") as fp:
        text = fp.read()
        assert "tofu" in text
        assert "veggie" not in text


def test_logdir(tmp_path, monkeypatch):
    import sattools.log
    monkeypatch.setenv("NAS_DATA", str(tmp_path))
    notnow = datetime.datetime(1900, 1, 1, 2, 3, 4)
    with unittest.mock.patch("datetime.datetime", autospec=True) as dd:
        dd.now.return_value = notnow
        d = sattools.log.logfile("saas", "grund")
    assert d == (tmp_path / "log" / "saas" /
                 "1900-01-01" / "grund-19000101T020304.log")
    assert d.parent.exists()
