"""Routines for interacting with typhon."""

import satpy.readers


def fileinfo2fspath(finfo):
    """Convert typhon FileInfo to satpy FSPath."""
    return satpy.readers.FSFile(finfo.path, fs=finfo.file_system)
