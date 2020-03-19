"""Utilities related to pytroll configuration
"""

import satpy.composites
import satpy.config
import pkg_resources
import pyresample


def get_all_areas(packages):
    """Get a dictionary with all findable areas
    """

    D = {}
    for pkg in packages:
        fn = pkg_resources.resource_filename(pkg, "etc/areas.yaml")
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
    satpy.config.recursive_dict_update(scn.dep_tree.composites, comps)
    satpy.config.recursive_dict_update(scn.dep_tree.mods, mods)


def add_all_pkg_comps_mods(scn, pkgs, sensors=["abi"]):
    """Add composites and modifiers to sensor dictionary for all packages

    See :func:`add_pkg_comps_mods`.
    """
    for pkg in pkgs:
        add_pkg_comps_mods(scn, pkg, sensors)
