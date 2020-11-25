import numpy
import pyresample


def join_areadefs(*areas):
    """Join one or more areadefinitions

    For a collection of areadefinitions sharing a projection and resolution,
    create the smallest area definition that encompasses all.
    """

    # also at https://github.com/pytroll/pyresample/pull/306

    first = None
    if len(areas) == 0:
        raise TypeError("Must pass at least one area, found zero.")
    for area in areas:
        if first is None:
            first = area
            largest_extent = list(area.area_extent)
        else:
            if not area.proj_dict == first.proj_dict:
                raise ValueError("Inconsistent projections between areas")
            if not numpy.isclose(area.resolution, first.resolution).all():
                raise ValueError("Inconsistent resolution between areas")
            largest_extent[0] = min(largest_extent[0], area.area_extent[0])
            largest_extent[1] = min(largest_extent[1], area.area_extent[1])
            largest_extent[2] = max(largest_extent[2], area.area_extent[2])
            largest_extent[3] = max(largest_extent[3], area.area_extent[3])

    return pyresample.create_area_def(
            area_id="joint-area",
            projection=first.proj_dict,
            units=first.proj_dict["units"],
            area_extent=largest_extent,
            resolution=first.resolution)


def flatten_areas(areas):
    """From areas and stacked areas, get all areas contained.
    """

    for ar in areas:
        if isinstance(ar, pyresample.geometry.StackedAreaDefinition):
            yield from flatten_areas(ar.defs)
        else:
            yield ar


def centre(area):
    """Get lat/lon of centre of area.
    """

    return area.get_lonlat(area.height//2, area.width//2)
