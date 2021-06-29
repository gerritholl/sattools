"""Show satellite ABI + GLM video with pytroll."""

import pathlib
import argparse
import logging

import pandas

from .. import vis
from .. import log
from .. import io


def _add_common_to_parser(parser):
    """Add common arguments to argument parser."""
    parser.add_argument(
            "--filename-pattern-image", action="store", type=str,
            default="{name:s}-{start_time:%Y%m%d_%H%M}.tiff",
            help="Filename pattern for output image files.")

    parser.add_argument(
            "--filename-pattern-video", action="store", type=str,
            default="{name:s}-{start_time:%Y%m%d_%H%M}-"
                    "{end_time:%Y%m%d_%H%M}.mp4",
            help="Filename pattern for output video files.")

    parser.add_argument(
            "--coastline-dir", action="store", type=str,
            help="Path to directory with coastlines.")


def get_parser_files():
    """Get the argument parser for passing files."""
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            "outdir", action="store", type=pathlib.Path,
            help="Directory where to write resulting images.")

    parser.add_argument(
            "files", action="store", type=pathlib.Path,
            nargs="+", help="Input satellite files (mix ABI and GLM)")

    _add_common_to_parser(parser)

    return parser


def get_parser_times():
    """Get the argument parser for passing times."""
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            "start_time", action="store", type=pandas.Timestamp)

    parser.add_argument(
            "end_time", action="store", type=pandas.Timestamp)

    parser.add_argument(
            "--area", action="store", type=str,
            help="Resample to this area")

    parser.add_argument(
            "--sector", action="store", type=str,
            help="Sector of ABI data to read",
            choices=("C", "F", "M1", "M2"))

    parser.add_argument(
            "--outdir", action="store", type=pathlib.Path,
            help="Directory where to write resulting images.",
            default=io.plotdir())

    _add_common_to_parser(parser)

    return parser


def parse_cmdline(get_parser=get_parser_files):
    """Parse the command line."""
    return get_parser().parse_args()


def video_files():
    """Parse commandline and call visualisation routines."""
    p = parse_cmdline(get_parser=get_parser_files)
    log.setup_main_handler(
        mods=("fogtools", "typhon", "fogpy", "sattools", "fcitools", "satpy",
              "pyresample"),
        level=logging.INFO)
    vis.show_video_abi_glm(
            files=p.files,
            img_out=p.filename_pattern_image,
            vid_out=p.filename_pattern_video,
            out_dir=p.outdir)
    print("Files written to:", p.outdir)


def video_times():
    """Parse commandline and call visualisation routines."""
    p = parse_cmdline(get_parser=get_parser_times)
    log.setup_main_handler(
        mods=("fogtools", "typhon", "fogpy", "sattools", "fcitools", "satpy",
              "pyresample"),
        level=logging.DEBUG)
    vis.show_video_abi_glm_times(
            start_date=p.start_time,
            end_date=p.end_time,
            img_out=p.filename_pattern_image,
            vid_out=p.filename_pattern_video,
            out_dir=p.outdir,
            sector=p.sector,
            area=p.area)
    print("Files written to:", p.outdir)
