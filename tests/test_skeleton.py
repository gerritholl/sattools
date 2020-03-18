# -*- coding: utf-8 -*-

import pytest
from sattools.skeleton import fib

__author__ = "Gerrit Holl"
__copyright__ = "Gerrit Holl"
__license__ = "mit"


def test_fib():
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(7) == 13
    with pytest.raises(AssertionError):
        fib(-10)
