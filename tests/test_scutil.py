import unittest.mock

def test_get_all_areas(fake_multiscene):
    from sattools.scutil import _get_all_areas_from_multiscene
    areas = _get_all_areas_from_multiscene(fake_multiscene)
    assert len(areas) == 3


@unittest.mock.patch("satpy.MultiScene.from_files", autospec=True)
def test_get_resampled_multiscene(sMf, tmp_path, fake_multiscene_empty, fake_multiscene2):
    from sattools.scutil import get_resampled_multiscene
    sMf.return_value = fake_multiscene_empty

    def load(ds_all, unload=None):
        for (sc, ref_sc) in zip(fake_multiscene_empty.scenes, fake_multiscene2.scenes):
            for ds in ds_all:
                sc[ds] = ref_sc[ds]

    fake_multiscene_empty.load = load
    ms = get_resampled_multiscene(
            [str(tmp_path / f"in{i:d}") for i in (1, 2, 3)],
            ["glm", "abi"],
            "C14",
            ["C14_flash_extent_density"])
    assert ms[0] is fake_multiscene_empty
    assert "C14" in ms[0].first_scene
    assert "C10" not in ms[0].first_scene
    sMf.assert_called_once_with(
            [str(tmp_path / f"in{i:d}") for i in (1, 2, 3)],
            reader=["glm", "abi"],
            ensure_all_readers=True,
            scene_kwargs={},
            group_keys=["start_time"],
            time_threshold=35)
    ms = get_resampled_multiscene(
            [str(tmp_path / f"in{i:d}") for i in (1, 2, 3)],
            ["glm", "abi"],
            "C08",
            ["C10"])
    assert "C10" in ms[0].first_scene

