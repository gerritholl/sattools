"""Utilities related to pytroll configuration
"""

import logging

import satpy.composites
import satpy.config
import pkg_resources
import pyresample

logger = logging.getLogger(__name__)


def get_all_areas(packages, missing_ok=False):
    """Get a dictionary with all findable areas
    """

    D = {}
    for pkg in packages:
        try:
            fn = pkg_resources.resource_filename(pkg, "etc/areas.yaml")
        except ModuleNotFoundError:
            if missing_ok:
                logger.exception(f"Cannot collect areas for {pkg:s}")
                continue
            else:
                raise

        # `load_area` does not currently give a sane error if a file does not
        # exist, see https://github.com/pytroll/pyresample/issues/250
        # manually test that file exists and can be read
        open(fn, "r").close()
        areas = pyresample.area_config.load_area(fn)
        D.update({ar.area_id: ar for ar in areas})
    return D


def add_pkg_comps_mods(scn, pkg, sensors=["abi"]):
    """Add composites and modifiers to sensor dictionary for one package

    Awaiting a solution to the issue at
    https://github.com/pytroll/satpy/issues/784 for a proper plugin system,
    this function will take an existing Scene object and makes it aware of
    composites and modifiers
    """
    p = pkg_resources.resource_filename(pkg, "etc/")
    cpl = satpy.composites.CompositorLoader(p)
    (comps, mods) = cpl.load_compositors(sensors)
    satpy.config.recursive_dict_update(scn.dep_tree.compositors, comps)
    satpy.config.recursive_dict_update(scn.dep_tree.modifiers, mods)


def add_all_pkg_comps_mods(scn, pkgs, sensors=["abi"]):
    """Add composites and modifiers to sensor dictionary for all packages

    See :func:`add_pkg_comps_mods`.
    """
    for pkg in pkgs:
        add_pkg_comps_mods(scn, pkg, sensors)
