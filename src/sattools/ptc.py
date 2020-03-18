"""Utilities related to pytroll configuration
"""

import pkg_resources
import pyresample


def get_all_areas(packages):
    """Get a dictionary with all findable areas
    """

    D = {}
    for pkg in packages:
        fn = pkg_resources.resource_filename(pkg, "etc/areas.yaml")
        areas = pyresample.area_config.load_area(fn)
        D.update({ar.area_id: ar for ar in areas})
    return D
