"""Utilities to get and manipulate scenes and multiscenes."""

import logging
import numbers

import satpy
import fsspec

from . import area
from . import glm
from . import abi
from . import log

logger = logging.getLogger(__name__)


def get_resampled_multiscene(files, reader, load_first, load_next,
                             scene_kwargs={}):
    """Get a multiscene resampled to the area covering all scenes in it.

    Given a list of files where area may vary between files, get a multiscene
    where each scene is resamled to the smallest enclosing area.  This is
    particularly useful when the multiscene consists of a range of ABI M1 and
    M2 scenes which may shift during the multiscene.

    Args:
        files (list of str or path): Files containing data.  Passed to
            ``satpy.MultiScene.from_files``.
        reader (List[str]): Readers to use.  Passed to
            ``satpy.MultiScene.from_files``.
        load_first (DataQuery, str, or numeric): Channel or wavelength, what
            dataset is loaded initially in order to calculate the joint area.
        load_next (list of DataQuery, str, or numeric): Channels or
            wavelengths, what datasets are loaded subsequently.
        scene_kwargs (Mapping): keyword arguments to pass to reader.  Passed to
            ``satpy.MultiScene.from_files``.

    Returns:
        (multiscene, resampled multiscene)
    """

    logger.info("Constructing multiscene")
    ms = satpy.MultiScene.from_files(
            [str(x) for x in files],
            reader=reader,
            ensure_all_readers=True,
            scene_kwargs=scene_kwargs,
            group_keys=["start_time"],
            time_threshold=35)  # every 10 minutes M1 starts 3 seconds late
    with log.RaiseOnWarnContext(logging.getLogger("satpy")):
        ms.load([load_first])
    logger.info("Calculating joint area")
    # turn warning message into error awaiting fix for
    # https://github.com/pytroll/satpy/issues/727
    with log.RaiseOnWarnContext(logging.getLogger("satpy")):
        # even though for the sake of area calculations it would be acceptable
        # to miss a scene here and there, I will want to load it for the
        # remaining scenes anyway for the safe of NUS calculation.  Even there
        # I don't technically need it for all scenes, only for those where I
        # need if for calculation of NUS-1, NUS-2, NUS-5, NUS-15, etc., but
        # that is becoming too complicated to bookkeep, so just ensure I have
        # them always.
        areas = set(area.flatten_areas(
            _get_all_areas_from_multiscene(ms, load_first)))
        joint = area.join_areadefs(*areas)
        ms.load(load_next, unload=False)
        # access to avoid https://github.com/pytroll/satpy/issues/1273
        # only here the warning message is actually logged
        # https://github.com/pytroll/satpy/issues/1444
        ms.scenes
    logger.info("Resampling")
    return (ms, ms.resample(joint, unload=False))


def _get_all_areas_from_multiscene(ms, datasets=None):
    S = set()
    if isinstance(datasets, (str, satpy.DataID, numbers.Real)):
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
    # FIXME: this is wrong; it's always choosing sector C even though
    # the ABI files are coming from M1 and M2, which may not even overlap...
    glm_files = list(glm.ensure_glm_for_period(
        start_date, end_date, sector="C"))
    (abi_fs, abi_files) = abi.get_fs_and_files(
            start_date, end_date, sector="M*", chans=chans)
    lfs = fsspec.implementations.local.LocalFileSystem()
    scene_kwargs = {
        "reader_kwargs": {
            "glm_l2": {"file_system": lfs},
            "abi_l1b": {"file_system": abi_fs}}}
    return (lfs, glm_files, abi_fs, abi_files, scene_kwargs)
