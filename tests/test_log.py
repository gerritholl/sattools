"""Test functionality related to logging."""
import datetime
import logging
import unittest.mock
import pytest


def test_setup_handler(tmp_path):
    """Test that setting up the logging handlers works."""
    import sattools.log
    sattools.log.setup_main_handler(
            ["banana"], filename=tmp_path / "test.log")
    logger = logging.getLogger("banana")
    assert len(logger.handlers) == 2


def test_log_context(tmp_path):
    """Test that the logging context such as to a file works."""
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
    """Test that we can get the log directory and it exists."""
    import sattools.log
    monkeypatch.setenv("NAS_DATA", str(tmp_path))
    notnow = datetime.datetime(1900, 1, 1, 2, 3, 4)
    with unittest.mock.patch("datetime.datetime", autospec=True) as dd:
        dd.now.return_value = notnow
        d = sattools.log.logfile("saas", "grund")
    assert d == (tmp_path / "log" / "saas" /
                 "1900-01-01" / "grund-19000101T020304.log")
    assert d.parent.exists()


def test_raise_on_warn_handler():
    """Test hack that raises when a warn handler is used."""
    import sattools.log
    rowh = sattools.log.RaiseOnWarnHandler()
    logger = logging.getLogger("testlogger")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(rowh)
    logger.debug("test")
    logger.info("test")
    with pytest.raises(sattools.log.WarningLoggedError,
                       match="my hovercraft is full of eels"):
        logger.warning("my hovercraft is full of eels")
    with pytest.raises(sattools.log.WarningLoggedError,
                       match="throatwobbler mangrove"):
        logger.error("throatwobbler mangrove")
    logger = logging.getLogger("otherlogger")
    logger.warning("nothing happens")


def test_setup_error_handler():
    """Test that seting up an error handler works."""
    import sattools.log
    sattools.log.setup_error_handler(["vuodnabahta"])
    logger = logging.getLogger("vuodnabahta.processing")
    with pytest.raises(sattools.log.WarningLoggedError,
                       match="het water is koud"):
        logger.warning("het water is koud")
    logger = logging.getLogger("vuodnabahta")
    logger.removeHandler(logger.handlers[0])
    assert not logger.handlers


def test_raise_on_warn_context():
    """Test raising on warning in a context manager."""
    import sattools.log
    logger = logging.getLogger("vuodnabahta.processing")
    logger.warning("the mantle is toxic")
    with sattools.log.RaiseOnWarnContext(logger):
        with pytest.raises(sattools.log.WarningLoggedError,
                           match="the mantle is toxic"):
            logger.warning("the mantle is toxic")
