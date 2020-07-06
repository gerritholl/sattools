import pathlib

import xarray
import numpy
import satpy


def show(
        files,
        channels,
        composites,
        regions,
        d_out,
        fn_out,
        reader=None,
        path_to_coastlines=None,
        label="",
        show_only_coastlines=False):
    """Visualise satellite data with pytroll

    From a set of files containing satellite data, visualise channels and
    composites for the given regions/areas, possibly adding coastlines.

    Args:
        files (List[pathlib.Path]):
            Paths to files

        composites (List[str]):
            List of composites to be generated

        channels (List[str]):
            List of channels (datasets) to be generated

        regions (List[str]):
            List of AreaDefinition strings or objects these shall be generated
            for.
            The special region 'native' means no reprojection is applied.

        d_out (pathlib.Path):
            Path to directory where output files shall be written.

        fn_out (str):
            Pattern of filename in output directory.  Using Python's string
            formatting syntax, the fields ``area`` and ``dataset`` will be
            replaced by the region/area and the composite/channel.

        reader (Optional[str]):
            What reader.  If none, let satpy figure it out.

        path_to_coastlines (Optional[str]):
            If given, directory to use for coastlines.

        label (Optiona[str]):
            Additional label to substitute into fn_out.

        show_only_coastlines (Optional[str or area]):
            If set, prepare images showing only coastlines.  May be
            set to either a channel name or composite for which the area will
            be taken for these images, or to an areadefinition that will be
            used.

    Returns:
        Set of paths written
    """
    L = set()
    sc = satpy.Scene(
            filenames=[str(f) for f in files],
            reader=reader)
    if path_to_coastlines is None:
        overlay = None
    else:
        overlay = {"coast_dir": path_to_coastlines, "color": "yellow"}
    sc.load(channels)
    sc.load(composites)
    if show_only_coastlines:
        try:
            da = sc[show_only_coastlines]
        except (KeyError, ValueError, TypeError):
            ar = show_only_coastlines
        else:
            ar = da.attrs["area"]
        sc["black"] = xarray.DataArray(
                numpy.zeros(shape=ar.shape),
                attrs=(atr := {"area": ar}))
        sc["white"] = xarray.DataArray(
                numpy.ones(shape=ar.shape),
                attrs=atr.copy())
        sc["nans"] = xarray.DataArray(
                numpy.full(shape=ar.shape, fill_value=numpy.nan),
                attrs=atr.copy())
    elif not sc.keys():
        return set()
    for la in regions:
        if la == "native":
            ls = sc
            arid = la
        else:
            ls = sc.resample(la)
            arid = ls[ls.keys().pop()].attrs["area"].area_id
        for dn in ls.keys():
            fn = pathlib.Path(d_out) / fn_out.format(
                    area=arid,
                    dataset=dn.name,
                    label=label)
            ls.save_dataset(
                    dn,
                    filename=str(fn),
                    overlay=overlay)
            L.add(fn)
    return L
