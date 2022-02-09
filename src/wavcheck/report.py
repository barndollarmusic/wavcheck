import sys

from .data import BwfMetadata, InternalState, WavMetadata
from .timecode import wall_secs_to_durstr

# TODO: Use a terminal color output library like Colorama to add colorful text
# for all print() calls.


def print_verbose_info(state: InternalState):
    """Prints verbose info for each read WAV file."""
    print()
    print("================================================================================")
    print("[wavcheck] Verbose Info for Read Files (-v, --verbose)")
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

    print(f"  Contains Broadcast Wave Format (BWF) v{bwf_data.version} Metadata: ")

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
        print((f"    [Loud] I {bwf_data.integrated_lufs} LUFS, "
               f"R {bwf_data.loudness_range_lu} LU, "
               f"S {bwf_data.max_short_term_lufs} LUFS, "
               f"M {bwf_data.max_momentary_lufs} LUFS, "
               f"P {bwf_data.max_dbtp} dBTP"))


def print_report(state: InternalState):
    """Prints summary information based on checks."""
    print(f"[wavcheck] Read {len(state.wav_files)} .wav files")

    num_warnings = state.warning_count()
    if num_warnings == 0:
        print("[wavcheck] SUCCESS: No warnings found. Happy scoring :)")
        sys.exit(0)

    print()
    print("================================================================================")
    print("[wavcheck] WARNINGS (you might want to check)")
    print("================================================================================")
    print()

    # TODO.
