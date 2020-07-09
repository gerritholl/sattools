from numpy.testing import assert_allclose


def test_join_areadefs():
    from sattools.area import join_areadefs
    from pyresample import create_area_def
    proj_dict = {'proj': 'geos', 'sweep': 'x', 'lon_0': 0, 'h': 35786023,
		 'x_0': 0, 'y_0': 0, 'ellps': 'GRS80', 'units': 'm',
		 'no_defs': None, 'type': 'crs'}

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

    ar_joined = join_areadefs(ar1, ar2, ar3)
    assert_allclose(ar_joined.area_extent, [0, 0, 120, 140])
