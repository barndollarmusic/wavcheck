import sys

from .read import WavMetadata


def check_wav_files(wav_list: list[WavMetadata]) -> int:
    """Checks WAV files for potential issues, printing a summary."""
    if len(wav_list) == 0:
        sys.exit("[wavcheck] ERROR: No .wav files found (or is this a John Cage thing?)")

    # TODO: Implement.

    return 0  # Success!
