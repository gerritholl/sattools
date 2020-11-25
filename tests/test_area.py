import pytest
import numpy.testing

from pyresample import create_area_def


def test_join_areadefs():
    from sattools.area import join_areadefs
    proj_dict = {'proj': 'geos', 'sweep': 'x', 'lon_0': 0, 'h': 35786023,
                 'x_0': 0, 'y_0': 0, 'ellps': 'GRS80', 'units': 'm',
                 'no_defs': None, 'type': 'crs'}
    proj_dict_alt = {'proj': 'laea', 'lat_0': -90, 'lon_0': 0, 'a': 6371228.0,
                     'units': 'm'}

    ar1 = create_area_def(
            "test-area",
            projection=proj_dict,
            units="m",
            area_extent=[0, 20, 100, 120],
            shape=(10, 10))

    ar2 = create_area_def(
            "test-area",
            projection=proj_dict,
            units="m",
            area_extent=[20, 40, 120, 140],
            shape=(10, 10))

    ar3 = create_area_def(
            "test-area",
            projection=proj_dict,
            units="m",
            area_extent=[20, 0, 120, 100],
            shape=(10, 10))

    ar4 = create_area_def(
            "test-area",
            projection=proj_dict_alt,
            units="m",
            area_extent=[20, 0, 120, 100],
            shape=(10, 10))

    ar5 = create_area_def(
            "test-area",
            projection=proj_dict,
            units="m",
            area_extent=[-50, -50, 50, 50],
            shape=(100, 100))

    ar_joined = join_areadefs(ar1, ar2, ar3)
    numpy.testing.assert_allclose(ar_joined.area_extent, [0, 0, 120, 140])
    with pytest.raises(ValueError):
        join_areadefs(ar3, ar4)
    with pytest.raises(ValueError):
        join_areadefs(ar3, ar5)
    with pytest.raises(TypeError):
        join_areadefs()


def test_centre():
    from sattools.area import centre

    proj_dict = {'proj': 'geos', 'sweep': 'x', 'lon_0': 0, 'h': 35786023,
                 'x_0': 0, 'y_0': 0, 'ellps': 'GRS80', 'units': 'm',
                 'no_defs': None, 'type': 'crs'}

    ar1 = create_area_def(
            "test-area",
            projection=proj_dict,
            units="m",
            area_extent=[0, 20, 100, 120],
            shape=(6, 15))

    ar2 = create_area_def(
            "test-area",
            projection=proj_dict,
            units="m",
            area_extent=[20, 40, 120, 140],
            shape=(15, 6))

    numpy.testing.assert_almost_equal(
            centre(ar1),
            (0.00044915764209268213, 0.0005576945108830417))

    numpy.testing.assert_almost_equal(
            centre(ar2),
            (0.0007036803060072213, 0.0008139325294262102))
