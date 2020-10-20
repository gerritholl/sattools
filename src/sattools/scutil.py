"""Utilities to get and manipulate scenes and multiscenes."""

import logging

import satpy
import fsspec

from . import area
from . import glm
from . import abi

logger = logging.getLogger(__name__)


def get_resampled_multiscene(files, reader, load_first, load_next,
                             scene_kwargs={}):
    """Get a multiscene resampled to the area covering all scenes in it.
    """

    logger.info("Constructing multiscene")
    ms = satpy.MultiScene.from_files(
            [str(x) for x in files],
            reader=["glm_l2", "abi_l1b"],
            ensure_all_readers=True,
            scene_kwargs=scene_kwargs,
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


def prepare_abi_glm_ms_args(start_date, end_date, chans):
    """Prepare args for ABI/GLM joint multiscene.

    Returns (glm_fs, glm_files, abi_fs, abi_files, scene_kwargs)
    """
    glmc_files = list(glm.ensure_glmc_for_period(start_date, end_date))
    (abi_fs, abi_files) = abi.get_fs_and_files(
            start_date, end_date, sector="M*", chans=chans)
    lfs = fsspec.implementations.local.LocalFileSystem()
    scene_kwargs = {
        "reader_kwargs": {
            "glm_l2": {"file_system": lfs},
            "abi_l1b": {"file_system": abi_fs}}}
    return (lfs, glmc_files, abi_fs, abi_files, scene_kwargs)
