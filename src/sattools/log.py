"""Utilities related to logging."""

import os
import sys
import logging
import datetime
import pathlib
import appdirs

logger = logging.getLogger(__name__)


class WarningLoggedError(Exception):
    pass


def setup_main_handler(
        mods=("fogtools", "typhon", "fogpy", "sattools", "fcitools"),
        level=logging.DEBUG,
        stderr=True,
        filename=None):
    """Setup the main handlers.

    By default, setups a stderr StreamHandler.  Optionally also sets up a
    FileHandler.

    Args:
        mods (Collection[str]): Modules to log for.
        level (logging level): At what level to log to stderr.
    """
    handlers = []
    if stderr:
        handlers.append(logging.StreamHandler(sys.stderr))
    if filename:
        handlers.append(logging.FileHandler(filename, encoding="utf-8"))
    formatter = logging.Formatter(
        "{asctime:s} {levelname:<8s} {name:s} "
        "{module:s}.{funcName:s}:{lineno:d}: {message:s}",
        style="{")
    for handler in handlers:
        handler.setFormatter(formatter)
    for m in mods:
        log = logging.getLogger(m)
        log.setLevel(level)
        for handler in handlers:
            log.addHandler(handler)


# this class is based on
# https://docs.python.org/3.10/howto/logging-cookbook.html#using-a-context-manager-for-selective-logging  # noqa: E501
class LoggingContext:
    def __init__(self, logger, level=None, handler=None, close=True):
        self.logger = logger
        self.level = level
        self.handler = handler
        self.close = close

    def __enter__(self):
        if self.level is not None:
            self.old_level = self.logger.level
            self.logger.setLevel(self.level)
        if self.handler:
            self.logger.addHandler(self.handler)

    def __exit__(self, et, ev, tb):
        if self.level is not None:
            self.logger.setLevel(self.old_level)
        if self.handler:
            self.logger.removeHandler(self.handler)
        if self.handler and self.close:
            self.handler.close()
        # implicit return of None => don't swallow exceptions


class LogToTimeFile(LoggingContext):
    """Logging context to log to a file

    This is intended to be used when files are processed, and a corresponding
    logfile shall be written.

    Example:

    with log.LogToTimeFile(logfile):
        ...
    """

    def __init__(self, logfile):
        logger = logging.getLogger()  # root logger
        self.logfile = logfile
        handler = logging.FileHandler(logfile, encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
                "{asctime:s} {name:s} {levelname:s} "
                "{processName:s}-{process:d} {threadName:s}-{thread:d} "
                "{pathname:s}:{lineno:d} {funcName:s}: {message:s}",
                style="{")
        handler.setFormatter(formatter)
        super().__init__(logger, level=logging.DEBUG, handler=handler,
                         close=True)

    def __enter__(self):
        super().__enter__()
        logger.info(f"Opening logfile at {self.logfile!s}")
        return self

    def __exit__(self, et, ev, tb):
        logger.info(f"Closing logfile at {self.logfile!s}")
        super().__exit__(et, ev, tb)


def logfile(name, label, create_dir=True):
    """Return filename to log to.

    I don't agree with appdirs.user_log_dir() which puts it in cache.
    Logging is permanent, caching is not.  Instead uses the NAS_DATA
    environment variable as a base.
    """
    now = datetime.datetime.now()
    basedir = pathlib.Path(
            os.environ.get(
                "NAS_DATA",
                appdirs.user_log_dir(opinion=False))
            )
    logfile = (basedir / "log" / name / f"{now:%Y-%m-%d}" /
               f"{label:s}-{now:%Y%m%dT%H%M%S}.log")
    if create_dir:
        logfile.parent.mkdir(exist_ok=True, parents=True)
    return logfile


class RaiseOnWarnHandler(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.WARNING:
            raise WarningLoggedError(
                    "A warning was logged with message " +
                    record.getMessage())


def setup_error_handler(mods=["satpy"]):
    """Setup a handler that turns log warnings into exceptions.

    By default only covers warnings issued by satpy.
    """

    rowh = RaiseOnWarnHandler()

    for m in mods:
        log = logging.getLogger(m)
        log.setLevel(logging.DEBUG)
        log.addHandler(rowh)


class RaiseOnWarnContext(LoggingContext):
    def __init__(self, logger):
        rowh = RaiseOnWarnHandler()
        super().__init__(logger, handler=rowh)
