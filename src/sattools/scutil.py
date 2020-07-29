"""Utilities to get and manipulate scenes and multiscenes."""


import satpy

import logging
logger = logging.getLogger(__name__)

from . import area

def get_resampled_multiscene(files, reader, load_first, load_next):
    """Get a multiscene resampled to the area covering all scenes in it.
    """

    logger.info("Constructing multiscene")
    ms = satpy.MultiScene.from_files(
            files,
            reader=["glm_l2", "abi_l1b"],
            ensure_all_readers=True,
            group_keys=["start_time"],
            time_threshold=35)  # every 10 minutes M1 starts 3 seconds late
    ms.load([load_first])
    logger.info("Calculating joint area")
    areas = set(area.flatten_areas(
        _get_all_areas_from_multiscene(ms, load_first)))
    joint = area.join_areadefs(*areas)
    ms.load(load_next, unload=False)
    ms.scenes  # access to avoid https://github.com/pytroll/satpy/issues/1273
    logger.info("Resampling")
    return (ms, ms.resample(joint, unload=False))


def _get_all_areas_from_multiscene(ms, datasets=None):
    S = set()
    if isinstance(datasets, (str, satpy.DataID)):
        datasets = [datasets]
    for sc in ms.scenes:
        for ds in datasets or sc.keys():
            try:
                S.add(sc[ds].attrs["area"])
            except KeyError:
                pass  # not an area-aware dataset
    return S
