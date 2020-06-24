import datetime
import logging
import io

import pytest
import numpy.testing


def test_setup_handler():
    import sattools.log
    sattools.log.setup_main_handler(["banana"])
    logger = logging.getLogger("banana")
    assert len(logger.handlers) == 1


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
