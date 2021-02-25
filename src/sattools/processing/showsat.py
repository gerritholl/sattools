"""Show satellite data with pytroll.
"""

import pathlib
import argparse
from .. import vis
from .. import log
from .. import ptc


def get_parser():
    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument(
            "outdir", action="store", type=pathlib.Path,
            help="Directory where to write resulting images.")

    parser.add_argument(
            "files", action="store", type=pathlib.Path,
            nargs="+", help="Input satellite files")

    parser.add_argument(
            "--composites", action="store", type=str,
            nargs="*",
            default=[],
            help="Composites to generate")

    parser.add_argument(
            "--channels", action="store", type=str,
            nargs="*",
            default=[],
            help="Channels to generate.  Should be FCI channel labels.")

    parser.add_argument(
            "-a", "--areas", action="store", type=str,
            nargs="+",
            help="Areas for which to generate those.")

    parser.add_argument(
            "--filename-pattern", action="store", type=str,
            default="{label:s}_{area:s}_{dataset:s}.tiff",
            help="Filename pattern for output files.")

    parser.add_argument(
            "--coastline-dir", action="store", type=str,
            help="Path to directory with coastlines.")

    parser.add_argument(
            "--show-only-coastlines", action="store_true",
            help="Prepare three blank images showing only coastlines.  "
                 "Backgrounds will be white, black, and transparent.")

    parser.add_argument(
            "-r", "--reader", action="store", type=str,
            help="What reader to use.  When not given. let Satpy "
                 "figure it out automatically.")

    return parser


def parse_cmdline():
    return get_parser().parse_args()


def main():
    p = parse_cmdline()
    log.setup_main_handler()
    areas = ptc.get_all_areas()
    files = vis.show(
            files=p.files,
            channels=p.channels,
            composites=p.composites,
            regions=[areas.get(area, area) for area in p.areas],
            d_out=p.outdir,
            reader=p.reader,
            fn_out=p.filename_pattern,
            path_to_coastlines=p.coastline_dir,
            show_only_coastlines=p.show_only_coastlines)
    print("Files written:", files)
