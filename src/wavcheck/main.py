import argparse
import pathlib
import sys

from .check import check_wav_files
from .fix import maybe_fix_wav_files
from .read import read_wav_files

__name__ = "wavcheck"
__version__ = "1.0.0"


# Command-line arguments:
parser = argparse.ArgumentParser(
    prog=__name__,
    description=("Check WAV files in a directory for potential "
                 "Broadcast Wave Format (BWF) problems."))
parser.add_argument("dir", nargs="?", default=".",
                    help="Directory with WAV files (defaults to the current dir)")
parser.add_argument("-v", "--version", action="version", version=__version__)


def cli():
    """Command-line interface."""

    # Parse command-line arguments for input directory to find WAV files in.
    args = parser.parse_args()

    d = pathlib.Path(args.dir).resolve()
    if not d.exists():
        sys.exit("[wavcheck] ERROR: input dir does not exist: '%s'" % d)
    if not d.is_dir():
        sys.exit("[wavcheck] ERROR: '%s' is not a directory" % d)

    # Read all WAV files in directory and check them for issues.
    wav_info_list = read_wav_files(d)
    status = check_wav_files(wav_info_list)

    # If applicable, prompt user to fix any correctible problems.
    maybe_fix_wav_files(wav_info_list)

    sys.exit(status)
