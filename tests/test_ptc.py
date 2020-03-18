from unittest.mock import patch


@patch("pyresample.area_config.load_area", autospec=True)
@patch("pkg_resources.resource_filename", autospec=True)
def test_get_areas(prf, pac):
    # need to mock pkg_resources.resource_filename
    # and pyresample.area_config.load_area
    # such that I get a list of areas
    import pyresample.geometry
    import sattools.ptc
    prf.return_value = "/dev/null"
    ad = pyresample.geometry.AreaDefinition(
            "shrubbery", "it is a good shrubbery", "shrub",
            {'ellps': 'WGS84', 'lat_0': '0', 'lat_ts': '0', 'lon_0': '0',
             'no_defs': 'None', 'proj': 'eqc', 'type': 'crs', 'units': 'm',
             'x_0': 0, 'y_0': 0},
            750, 300, (2500000, 4000000, 3000000, 40000000))
    pac.return_value = [ad]
    D = sattools.ptc.get_all_areas(["tofu", "tempeh"])
    assert prf.call_count == 2
    assert pac.call_count == 2
    assert D == {"shrubbery": ad}
