import logging

import pytest
from unittest.mock import patch, MagicMock

fake_areas = ["""
new-england-2000:
  description: New England, 2000 metre
  projection:
    proj: eqc
    ellps: WGS84
    units: m
  shape:
    width: 897
    height: 585
  area_extent:
    lower_left_xy: [-9163411, 4255208]
    upper_right_xy: [-7369792, 5424479]""",
"""new-england-3000:
  description: New England, 3000 metre
  projection:
    proj: eqc
    ellps: WGS84
    units: m
  shape:
    width: 598
    height: 390
  area_extent:
    lower_left_xy: [-9163411, 4255208]
    upper_right_xy: [-7369792, 5424479]
"""]

def test_get_areas(caplog, tmp_path):

    import satpy
    import pyresample.geometry
    import sattools.ptc
    for (nm, ar) in zip("ab", fake_areas):
        (tmp_path / nm / "etc").mkdir(parents=True)
        with (tmp_path / nm / "areas.yaml").open(mode="wt") as fp:
            fp.write(ar)

    with satpy.config.set(config_path=[tmp_path / "a", tmp_path / "b"]):
        D = sattools.ptc.get_all_areas()
    assert "new-england-2000" in D  # first
    assert "new-england-3000" in D  # second
    assert "germ" in D  # builtin
