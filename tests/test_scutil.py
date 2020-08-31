def test_get_all_areas(fake_multiscene):
    from sattools.scutil import _get_all_areas_from_multiscene
    areas = _get_all_areas_from_multiscene(fake_multiscene)
    assert len(areas) == 3
