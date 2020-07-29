import pathlib

import xarray
import numpy
import satpy
import pyresample.geometry
import logging

from . import area
from . import scutil

logger = logging.getLogger(__name__)

decorate_args = {
        "decorate": [
            {"text": {
                "txt": "{start_time:%Y-%m-%d %H:%M}",
                "align": {
                    "top_bottom": "bottom",
                    "left_right": "right"},
                "font": '/usr/share/fonts/truetype/arial.ttf',
                "font_size": 20,
                "height": 30,
                "bg": "black",
                "bg_opacity": 255,
                "line": "white"}}]}

overlay_args = {
        "coast_dir": "/media/nas/x21308/shp/",
        "overlays": {
            "coasts": {
                "outline": (255, 255, 0),
                "width": 1.5,
                "level": 1,
                "resolution": "f"},
            "rivers": {
                "outline": (0, 0, 255),
                "width": 1.5,
                "level": 5,
                "resolution": "f"},
            "borders": {
                "outline": (0, 0, 0),
                "width": 1.5,
                "level": 3,
                "resolution": "f"}}}

enh_args = {"decorate": decorate_args, "overlay": overlay_args}


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
                    dataset=dn["name"],
                    label=label)
            ls.save_dataset(
                    dn,
                    filename=str(fn),
                    overlay=overlay)
            L.add(fn)
    return L


def show_video_abi_glm(
        files, out_dir,
        img_out="{name:s}-{start_time:%Y%m%d_%H%M}.tiff",
        vid_out="{name:s}-{start_time:%Y%m%d_%H%M}-"
                "{end_time:%Y%m%d_%H%M}.mp4"):
    """Show a video.

    Show a video with ABI MESO and GLM L2 C14_flash_extent_density.
    """

    (ms, mr) = scutil.get_resampled_multiscene(
            files,
            reader=["glm_l2", "abi_l1b"],
            load_first="C14",
            load_next=["C14_flash_extent_density"])

    logger.info("Making an image")
    for (sc2, sc3) in zip(ms.scenes, mr.scenes):
        if isinstance(sc2["C14"].attrs["area"],
                      pyresample.geometry.StackedAreaDefinition):
            sc3.save_datasets(
                filename=str(out_dir / img_out),
                overlay=enh_args["overlay"])
            break
    else:
        raise ValueError("Never found a joint scene :(")
    logger.info("Making a video")
    mr.save_animation(str(out_dir / vid_out), enh_args=enh_args)
