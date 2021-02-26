"""Utilities related to pytroll configuration."""

import logging
import os.path

import pkg_resources
import satpy
import pyresample

logger = logging.getLogger(__name__)


def get_all_areas():
    """Get a dictionary with all findable areas.

    This relies on the satpy configuration path being set correctly.
    """
    core = pkg_resources.resource_filename("satpy", "etc/areas.yaml")
    others = [os.path.join(x, "areas.yaml") for x in
              satpy.config["config_path"]]
    D = {}
    for fn in [core] + others:
        areas = pyresample.area_config.load_area(fn)
        if isinstance(areas, pyresample.AreaDefinition):
            # load_area doesn't return a list if it's just one...
            areas = [areas]
        D.update({ar.area_id: ar for ar in areas})
    return D
