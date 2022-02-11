# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import pathlib
import sys

from .check import check_wav_files
from .data import Context
from .fix import maybe_fix_wav_files
from .read import read_or_prompt_framerate, read_wav_files
from .report import print_report, print_verbose_info

__name__ = "wavcheck"
__version__ = "0.9.1"  # NOTE: Also update setup.cfg when updating version.


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
    args = parser.parse_args()

    # Resolve input directory to find WAV files in.
    d = pathlib.Path(args.dir).resolve()
    if not d.exists():
        sys.exit(f"[wavcheck] ERROR: input dir does not exist: '{d}'")
    if not d.is_dir():
        sys.exit(f"[wavcheck] ERROR: '{d}' is not a directory")

    ctx = Context(d, args.verbose or False)

    # Determine framerate.
    ctx.frame_rate = read_or_prompt_framerate(ctx, args.framerate or "")
    print(
        f"[wavcheck] Interpreting timecodes using frame rate {ctx.frame_rate}")

    # Read all WAV files in directory and check them for issues.
    state = read_wav_files(ctx)
    print(f"[wavcheck] Read {len(state.wav_files)} .wav files")
    check_wav_files(ctx, state)

    if args.verbose:
        print_verbose_info(ctx, state)
    print_report(ctx, state)

    # If applicable, prompt user to fix any correctible problems.
    maybe_fix_wav_files(ctx, state)

    num_warnings = state.warning_count()
    if num_warnings == 0:
        print("\n[wavcheck] SUCCESS: No warnings found. Happy scoring :)\n")

    sys.exit(num_warnings)
