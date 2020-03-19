import pytest
from unittest.mock import patch, MagicMock


def test_get_areas():
    # need to mock pkg_resources.resource_filename
    # and pyresample.area_config.load_area
    # such that I get a list of areas
    import pyresample.geometry
    import sattools.ptc
    ad = pyresample.geometry.AreaDefinition(
            "shrubbery", "it is a good shrubbery", "shrub",
            {'ellps': 'WGS84', 'lat_0': '0', 'lat_ts': '0', 'lon_0': '0',
             'no_defs': 'None', 'proj': 'eqc', 'type': 'crs', 'units': 'm',
             'x_0': 0, 'y_0': 0},
            750, 300, (2500000, 4000000, 3000000, 40000000))
    with patch("pkg_resources.resource_filename", autospec=True) as prf:
        prf.return_value = "/dev/null"
        with patch("pyresample.area_config.load_area", autospec=True) as pal:
            pal.return_value = [ad]
            D = sattools.ptc.get_all_areas(["tofu", "tempeh"])
            assert prf.call_count == 2
            assert pal.call_count == 2
            assert D == {"shrubbery": ad}
        prf.return_value = "/file/not/found"
        with pytest.raises(FileNotFoundError):
            sattools.ptc.get_all_areas(["oranges"])


def test_add_pkg():
    import sattools.ptc
    scn = MagicMock()
    with patch("satpy.composites.CompositorLoader", autospec=True) as scC, \
            patch("pkg_resources.resource_filename", autospec=True) as prf:
        prf.return_value = "/dev/null"
        scC.return_value.load_compositors.return_value = ({}, {})
        sattools.ptc.add_pkg_comps_mods(scn, "apple", ["tomato"])


def test_add_pkgs():
    import sattools.ptc
    scn = MagicMock()
    with patch("sattools.ptc.add_all_pkg_comps_mods", autospec=True):
        sattools.ptc.add_all_pkg_comps_mods(
                scn, ["apple", "strawberry"], ["tomato"])
