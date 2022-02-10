import collections
from gc import collect
import sys

from .data import BwfMetadata, CrossFileCheck, InternalState, WavFileCheck, WavFileState, WavMetadata
from .timecode import wall_secs_to_durstr

# TODO: Use a terminal color output library like Colorama to add colorful text
# for all print() calls.


def print_verbose_info(state: InternalState):
    """Prints verbose info for each read WAV file."""
    print()
    print("================================================================================")
    print("[wavcheck] Verbose Info for Read WAV Files (-v, --verbose)")
    print("================================================================================")
    print()

    for filename in state.wav_files:
        wav_file = state.wav_files[filename]

        print(filename)
        print((f"  {wav_file.metadata.bit_depth} bit, "
               f"{wav_file.metadata.sample_rate_hz / 1000.0} kHz, "
               f"{wav_file.metadata.num_chans} channels, "
               f"{wall_secs_to_durstr(wav_file.metadata.duration_secs)}"))

        _print_verbose_bwf_info(wav_file.metadata)
        print()


def _print_verbose_bwf_info(wav_data: WavMetadata):
    """Prints verbose info for this BWF metadata."""
    bwf_data = wav_data.bwf_data
    if bwf_data is None:
        print("  MISSING Broadcast Wave Format (BWF) Metadata (Timecode, UMID, Loudness)")
        return

    print(
        f"  Contains Broadcast Wave Format (BWF) v{bwf_data.version} Metadata: ")

    # TODO: Read or input frame rate information from the user to support
    # outputting timecode values here.
    start_samples = bwf_data.samples_since_origin
    start_secs = float(start_samples) / wav_data.sample_rate_hz
    print((f"    [Time] Start: {start_samples} samples "
           f"({wall_secs_to_durstr(start_secs)}) after 00:00:00:00"))

    print((f"    [Orig] {bwf_data.originator} {bwf_data.originator_reference} "
           f"{bwf_data.origination_date} {bwf_data.origination_time}"))
    print(f"    [Desc] {bwf_data.description}")
    print(f"    [Hist] {bwf_data.coding_history}")

    if bwf_data.version >= 1:
        print(f"    [UMID] {bwf_data.umid_base64}")
    if bwf_data.version >= 2:
        print(f"    [Loud] {_loudness_summary(bwf_data)}")


def _loudness_summary(bwf_data: BwfMetadata) -> str:
    """Returns short string summary of BWF loudness stats."""
    return (f"I {bwf_data.integrated_lufs} LUFS, "
            f"R {bwf_data.loudness_range_lu} LU, "
            f"S {bwf_data.max_short_term_lufs} LUFS, "
            f"M {bwf_data.max_momentary_lufs} LUFS, "
            f"P {bwf_data.max_dbtp} dBTP")


def print_report(state: InternalState):
    """Prints summary information based on checks."""
    print(f"[wavcheck] Read {len(state.wav_files)} .wav files")

    num_warnings = state.warning_count()
    if num_warnings == 0:
        print("[wavcheck] SUCCESS: No warnings found. Happy scoring :)\n")
        sys.exit(0)

    print()
    print("================================================================================")
    print("[wavcheck] WARNINGS (you might want to check)")
    print("================================================================================")
    print()

    # Cross-file checks:
    for cross_check in state.failed_cross_checks:
        _print_cross_check(cross_check, state)

    # Per-file checks:
    for filename in state.wav_files:
        if len(state.wav_files[filename].failed_checks) == 0:
            continue

        print(f"!! Warnings for {filename}:")
        for file_check in state.wav_files[filename].failed_checks:
            _print_file_check(file_check, state.wav_files[filename])  # TODO.
        print()

    print()


def _print_cross_check(cross_check: CrossFileCheck, state: InternalState):
    """Prints warning information for the given cross-file check."""
    if cross_check == CrossFileCheck.MULTIPLE_BIT_DEPTHS:
        bit_depths: set[int] = set()
        for filename in state.wav_files:
            bit_depths.add(state.wav_files[filename].metadata.bit_depth)
        print(f"!! Multiple bit depths found: {bit_depths}")
        return

    if cross_check == CrossFileCheck.MULTIPLE_SAMPLE_RATES:
        sample_rates: set[int] = set()
        for filename in state.wav_files:
            sample_rates.add(state.wav_files[filename].metadata.sample_rate_hz)
        print(f"!! Multiple sample rates found: {sample_rates}")
        return

    if cross_check == CrossFileCheck.NON_UNIQUE_UMIDS:
        umids = collections.defaultdict(list)
        for filename in state.wav_files:
            metadata = state.wav_files[filename].metadata
            if metadata.bwf_data is not None and metadata.bwf_data.version >= 1:
                umids[metadata.bwf_data.umid_base64].append(filename)

        for umid in umids:
            if len(umids[umid]) >= 2:
                print(
                    f"!! These files have the same UMID (pass -v or --verbose for more info):")
                print(f"    {umids[umid]}")


def _print_file_check(file_check: WavFileCheck, wav_state: WavFileState):
    """Prints warning information for the given file-specific check."""
    metadata = wav_state.metadata

    if file_check == WavFileCheck.LOW_BIT_DEPTH:
        print(f"    Low bit-depth: {metadata.bit_depth}")
        return

    if file_check == WavFileCheck.LOW_SAMPLE_RATE:
        print(f"    Low sample rate: {metadata.sample_rate_hz}")
        return

    if file_check == WavFileCheck.VERY_SHORT_DURATION:
        print(f"    Very short duration: {metadata.duration_secs} secs")
        return

    if file_check == WavFileCheck.MISSING_BWF:
        print("    Missing Broadcast Wave Format (BWF) metadata")
        return

    if file_check == WavFileCheck.STARTS_AT_TIME_ZERO:
        print("    BWF: Starts at timecode 00:00:00:00")
        return

    if file_check == WavFileCheck.MISSING_UMID:
        print("    BWF: Missing Unique Material Identifier (UMID)")
        return

    if file_check == WavFileCheck.UNNATURALLY_LOUD:
        print("    BWF: Has at least 1 unnaturally loud stat")
        print(f"         {_loudness_summary(metadata.bwf_data)}")
        return
