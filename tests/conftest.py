# -*- coding: utf-8 -*-
"""
    Dummy conftest.py for sattools.

    If you don't know what this is for, just leave it empty.
    Read more about conftest.py under:
    https://pytest.org/latest/plugins.html
"""

import pytest
import os

@pytest.fixture(autouse=True)
def setUp(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "scratch"))


