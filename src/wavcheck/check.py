import collections
import sys

from .data import CrossFileCheck, InternalState
from .data import WavFileCheck
from .data import WavFileState


def check_wav_files(state: InternalState):
    """Checks WAV files for potential issues."""
    if len(state.wav_files) == 0:
        sys.exit(
            "[wavcheck] ERROR: No .wav files found (or is this a John Cage thing?)")

    # Per-file checks:
    bit_depths: set[int] = set()
    sample_rates: set[int] = set()
    umid_counts = collections.Counter()

    for filename in state.wav_files:
        wav_file = state.wav_files[filename]
        _check_wav_file(wav_file)

        bit_depths.add(wav_file.metadata.bit_depth)
        sample_rates.add(wav_file.metadata.sample_rate_hz)
        if not WavFileCheck.MISSING_UMID in wav_file.failed_checks:
            umid_counts[wav_file.metadata.bwf_data.umid_base64] += 1

    # Cross-file checks:
    if len(bit_depths) >= 2:
        state.failed_cross_checks.append(CrossFileCheck.MULTIPLE_BIT_DEPTHS)
    if len(sample_rates) >= 2:
        state.failed_cross_checks.append(CrossFileCheck.MULTIPLE_SAMPLE_RATES)
    for umid in umid_counts:
        if umid_counts[umid] >= 2:
            state.failed_cross_checks.append(CrossFileCheck.NON_UNIQUE_UMIDS)
            break
    # TODO: Verify potential framerates based on TC in filenames across files.


def _check_wav_file(wav_state: WavFileState):
    """Performs per-file checks for one WAV file."""

    # Basic WAV metadata checks:
    if wav_state.metadata.bit_depth < 16:
        wav_state.failed_checks.append(WavFileCheck.LOW_BIT_DEPTH)

    if wav_state.metadata.sample_rate_hz < 44100:
        wav_state.failed_checks.append(WavFileCheck.LOW_SAMPLE_RATE)

    if wav_state.metadata.duration_secs < 1.0:
        wav_state.failed_checks.append(WavFileCheck.VERY_SHORT_DURATION)

    # Broadcast Wave Format checks:
    bwf_data = wav_state.metadata.bwf_data
    if bwf_data is None:
        wav_state.failed_checks.append(WavFileCheck.MISSING_BWF)
        return

    if bwf_data.samples_since_origin == 0:
        wav_state.failed_checks.append(WavFileCheck.STARTS_AT_TIME_ZERO)

    # TODO: Add support for checking start time against HHMMSSFF in filename.

    if (bwf_data.version == 0 or _is_all_zeros(bwf_data.umid)):
        wav_state.failed_checks.append(WavFileCheck.MISSING_UMID)
    
    if bwf_data.version < 2:
        return
    
    if (bwf_data.max_dbtp >= -0.3
            or bwf_data.max_momentary_lufs >= -3.0
            or bwf_data.max_short_term_lufs >= -6.0
            or bwf_data.integrated_lufs >= -9.0):
        wav_state.failed_checks.append(WavFileCheck.UNNATURALLY_LOUD)


def _is_all_zeros(data: bytes) -> bool:
    """Returns True if data is empty or consists of all zeros."""
    for i in data:
        if i != 0:
            return False
    return True
