"""Show satellite ABI + GLM video with pytroll."""

import pathlib
import argparse
import logging
from .. import vis
from .. import log


def get_parser():
    """Get the argument parser."""
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            "outdir", action="store", type=pathlib.Path,
            help="Directory where to write resulting images.")

    parser.add_argument(
            "files", action="store", type=pathlib.Path,
            nargs="+", help="Input satellite files (mix ABI and GLM)")

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

    return parser


def parse_cmdline():
    """Parse the command line."""
    return get_parser().parse_args()


def main():
    """Parse commandline and call visualisation routines."""
    p = parse_cmdline()
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
