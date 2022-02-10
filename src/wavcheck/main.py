import argparse
import pathlib
import sys

from .check import check_wav_files
from .fix import maybe_fix_wav_files
from .read import read_wav_files
from .report import print_report, print_verbose_info

__name__ = "wavcheck"
__version__ = "1.0.0"


# Command-line arguments:
parser = argparse.ArgumentParser(
    prog=__name__,
    description=("Check WAV files in a directory for potential "
                 "Broadcast Wave Format (BWF) problems."))
parser.add_argument("--version", action="version", version=__version__)
parser.add_argument("-v", "--verbose", action=argparse.BooleanOptionalAction,
                    help="Print verbose info for each file")
parser.add_argument("dir", nargs="?", default=".",
                    help="Directory with WAV files (defaults to current dir)")


def cli():
    """Command-line interface."""
    # Parse command-line arguments for input directory to find WAV files in.
    args = parser.parse_args()
    args.verbose = args.verbose or False

    d = pathlib.Path(args.dir).resolve()
    if not d.exists():
        sys.exit(f"[wavcheck] ERROR: input dir does not exist: '{d}'")
    if not d.is_dir():
        sys.exit(f"[wavcheck] ERROR: '{d}' is not a directory")

    # Read all WAV files in directory and check them for issues.
    state = read_wav_files(d, args.verbose)
    print(f"[wavcheck] Read {len(state.wav_files)} .wav files")
    check_wav_files(state)

    if args.verbose:
        print_verbose_info(state)
    print_report(state)

    # If applicable, prompt user to fix any correctible problems.
    maybe_fix_wav_files(state)

    sys.exit(state.warning_count())
