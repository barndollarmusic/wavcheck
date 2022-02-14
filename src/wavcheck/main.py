# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import pathlib
import sys

from .check import check_wav_files
from .data import Context
from .fix import maybe_fix_wav_files
from .print import print_error_exit, print_info, print_init, print_success_exit
from .read import read_or_prompt_framerate, read_wav_files
from .report import report_check_results

__name__ = "wavcheck"
__version__ = "0.9.3"  # NOTE: Also update setup.cfg when updating version.


# Command-line arguments:
parser = argparse.ArgumentParser(
    prog=__name__,
    description=("Check WAV files in a directory for potential "
                 "Broadcast Wave Format (BWF) problems."))
parser.add_argument("-f", "--framerate",
                    help='Framerate (e.g. "23.976 non-drop") or a file containing it')
parser.add_argument("--version", action="version", version=__version__)
parser.add_argument("-v", "--verbose", action=argparse.BooleanOptionalAction,
                    help="Print verbose info for each file")
parser.add_argument("dir", nargs="?", default=".",
                    help="Directory with WAV files (defaults to current dir)")


def cli():
    """Command-line interface."""
    print_init()
    args = parser.parse_args()

    # Resolve input directory to find WAV files in.
    d = pathlib.Path(args.dir).resolve()
    if not d.exists():
        print_error_exit(f"input dir does not exist: '{d}'")
    if not d.is_dir():
        print_error_exit(f"'{d}' is not a directory")

    ctx = Context(d, args.verbose or False)

    # Determine framerate.
    ctx.frame_rate = read_or_prompt_framerate(ctx, args.framerate or "")
    print_info(f"Interpreting timecodes using frame rate {ctx.frame_rate}\n")

    # Read all WAV files in directory and check them for issues.
    state = read_wav_files(ctx)
    print_info(f"Read {len(state.wav_files)} .wav files")
    check_wav_files(ctx, state)
    report_check_results(ctx, state)

    # If applicable, prompt user to fix any correctible problems.
    maybe_fix_wav_files(ctx, state)

    num_warnings = state.warning_count()
    if num_warnings == 0:
        print_success_exit("No warnings found. Happy scoring :)\n")

    sys.exit(num_warnings)
