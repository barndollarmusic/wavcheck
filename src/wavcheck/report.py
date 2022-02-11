# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import collections
import sys

from .data import BwfMetadata, Context, CrossFileCheck, InternalState, KSDATAFORMAT_SUBTYPE_PCM, SupportedFormatTag, WavFileCheck, WavFileState, WavMetadata
from .timecode import wall_secs_to_durstr, wall_secs_to_fractional_frame_idx, wall_secs_to_tc_left

# TODO: Use a terminal color output library like Colorama to add colorful text
# for all print() calls.


def print_verbose_info(ctx: Context, state: InternalState):
    """Prints verbose info for each read WAV file."""
    print()
    print("================================================================================")
    print("[wavcheck] Verbose Info for Read WAV Files (-v, --verbose)")
    print("================================================================================")
    print()

    for filename in state.wav_files:
        wav_file = state.wav_files[filename]

        print(filename)
        _print_detected_timecode_in_filename(ctx, wav_file.metadata)
        print((f"  {wav_file.metadata.fmt_data.bit_depth} bit, "
               f"{wav_file.metadata.fmt_data.sample_rate_hz / 1000.0} kHz, "
               f"{wav_file.metadata.fmt_data.num_chans} channels, "
               f"{wall_secs_to_durstr(wav_file.metadata.duration_secs())}"))

        _print_verbose_bwf_info(ctx, wav_file.metadata)
        print()


def _print_detected_timecode_in_filename(ctx: Context, wav_data: WavMetadata):
    """Prints verbose info for timecode detected in filename."""
    tc_str = "(none recognized)"
    if wav_data.tc_in_filename is not None:
        tc_str = str(wav_data.tc_in_filename.tc)
    print(f"  Timecode in Filename: {tc_str}")


def _print_verbose_bwf_info(ctx: Context, wav_data: WavMetadata):
    """Prints verbose info for this BWF metadata."""
    bwf_data = wav_data.bwf_data
    if bwf_data is None:
        print("  MISSING Broadcast Wave Format (BWF) Metadata (Timecode, UMID, Loudness)")
        return

    print(
        f"  Contains Broadcast Wave Format (BWF) v{bwf_data.version} Metadata: ")

    start_samples = bwf_data.samples_since_origin
    start_secs = wav_data.bwf_start_time_secs(ctx.frame_rate)
    start_tc = wall_secs_to_tc_left(start_secs, ctx.frame_rate)

    fractional_frames_msg = ""
    fractional_frames = wall_secs_to_fractional_frame_idx(
        start_secs, ctx.frame_rate) % 1.0
    if fractional_frames > 0.01:
        fractional_frames_msg = f" and {fractional_frames:0.3f} FRACTIONAL FRAME"

    print((f"    [Time] Start: {start_samples} samples "
           f"({wall_secs_to_durstr(start_secs)} wall time) after 00:00:00:00"))
    print((f"                  (interpreted as {start_tc}{fractional_frames_msg} "
           f"in {ctx.frame_rate})"))

    print((f"    [Orig] {bwf_data.originator} {bwf_data.originator_reference} "
           f"{bwf_data.origination_date} {bwf_data.origination_time}"))
    print(f"    [Desc] {bwf_data.description}")
    print(f"    [Hist] {bwf_data.coding_history}")

    if bwf_data.version >= 1:
        print(f"    [UMID] {bwf_data.umid_hex}")
    if bwf_data.version >= 2:
        print(f"    [Loud] {_loudness_summary(bwf_data)}")


def _loudness_summary(bwf_data: BwfMetadata) -> str:
    """Returns short string summary of BWF loudness stats."""
    return (f"I {bwf_data.integrated_lufs} LUFS, "
            f"R {bwf_data.loudness_range_lu} LU, "
            f"S {bwf_data.max_short_term_lufs} LUFS, "
            f"M {bwf_data.max_momentary_lufs} LUFS, "
            f"P {bwf_data.max_dbtp} dBTP")


def print_report(ctx: Context, state: InternalState):
    """Prints summary information based on checks."""
    num_warnings = state.warning_count()
    if num_warnings == 0:
        return

    print()
    print("================================================================================")
    print("[wavcheck] WARNINGS (you might want to check)")
    print("================================================================================")
    print()

    # Cross-file checks:
    for cross_check in state.failed_cross_checks:
        _print_cross_check(cross_check, state)

    print()

    # Per-file checks:
    for filename in state.wav_files:
        if len(state.wav_files[filename].failed_checks) == 0:
            continue

        print(f"!! Warnings for {filename}:")
        for file_check in state.wav_files[filename].failed_checks:
            _print_file_check(ctx, file_check, state.wav_files[filename])
        print()

    print()


def _print_cross_check(cross_check: CrossFileCheck, state: InternalState):
    """Prints warning information for the given cross-file check."""
    if cross_check == CrossFileCheck.MULTIPLE_BIT_DEPTHS:
        bit_depths: set[int] = set()
        for filename in state.wav_files:
            bit_depths.add(
                state.wav_files[filename].metadata.fmt_data.bit_depth)
        print(f"!! Multiple bit depths found: {bit_depths}")
        return

    if cross_check == CrossFileCheck.MULTIPLE_SAMPLE_RATES:
        sample_rates: set[int] = set()
        for filename in state.wav_files:
            sample_rates.add(
                state.wav_files[filename].metadata.fmt_data.sample_rate_hz)
        print(f"!! Multiple sample rates found: {sample_rates}")
        return

    if cross_check == CrossFileCheck.NON_UNIQUE_UMIDS:
        umids = collections.defaultdict(list)
        for filename in state.wav_files:
            metadata = state.wav_files[filename].metadata
            if metadata.bwf_data is not None and metadata.bwf_data.version >= 1:
                umids[metadata.bwf_data.umid_hex].append(filename)

        for umid in umids:
            if len(umids[umid]) >= 2:
                print(
                    f"!! These files have the same UMID (pass -v or --verbose for more info):")
                print(f"    {umids[umid]}")


def _print_file_check(ctx: Context, file_check: WavFileCheck, wav_state: WavFileState):
    """Prints warning information for the given file-specific check."""
    metadata = wav_state.metadata

    if file_check == WavFileCheck.NONSTANDARD_FORMAT:
        if metadata.fmt_data.format_tag == SupportedFormatTag.WAVE_FORMAT_EXTENSIBLE:
            print(("    WAVE_FORMAT_EXTENSIBLE should be used with "
                   f"KSDATAFORMAT_SUBTYPE_PCM (0x{KSDATAFORMAT_SUBTYPE_PCM.hex().upper()}); "
                   f"found: 0x{metadata.fmt_data.ext_sub_format.hex().upper()}"))
            return
        else:
            print(
                f"    Nonstandard FormatTag: 0x{format(metadata.fmt_data.format_tag, 'X')}")
            return

    if file_check == WavFileCheck.LOW_BIT_DEPTH:
        print(f"    Low bit-depth: {metadata.fmt_data.bit_depth}")
        return

    if file_check == WavFileCheck.LOW_SAMPLE_RATE:
        print(f"    Low sample rate: {metadata.fmt_data.sample_rate_hz}")
        return

    if file_check == WavFileCheck.VERY_SHORT_DURATION:
        print(f"    Very short duration: {metadata.duration_secs()} secs")
        return

    if file_check == WavFileCheck.MISSING_BWF:
        print("    Missing Broadcast Wave Format (BWF) metadata")
        return

    if file_check == WavFileCheck.STARTS_AT_TIME_ZERO:
        print("    BWF: Starts at timecode 00:00:00:00")
        return

    if file_check == WavFileCheck.FRACTIONAL_FRAME_START_TC:
        start_secs = wav_state.metadata.bwf_start_time_secs(ctx.frame_rate)
        bwf_tc = wall_secs_to_tc_left(start_secs, ctx.frame_rate)
        fractional_frames = wall_secs_to_fractional_frame_idx(
            start_secs, ctx.frame_rate) % 1.0
        fraction_str = f"{fractional_frames:.3f}".lstrip("0")
        print(f"    BWF: Starts on fractional frame {bwf_tc}{fraction_str}")
        print(f"         (as interpreted in {ctx.frame_rate})")

    if file_check == WavFileCheck.MISSING_UMID:
        print("    BWF: Missing Unique Material Identifier (UMID)")
        return

    if file_check == WavFileCheck.UNNATURALLY_LOUD:
        print("    BWF: Has at least 1 unnaturally loud stat")
        print(f"         {_loudness_summary(metadata.bwf_data)}")
        return

    if file_check == WavFileCheck.FILENAME_TC_MISMATCH:
        start_secs = wav_state.metadata.bwf_start_time_secs(ctx.frame_rate)
        bwf_tc = wall_secs_to_tc_left(start_secs, ctx.frame_rate)
        print(
            f"    BWF: Start timecode {bwf_tc} (in {ctx.frame_rate}) doesn't match")
        print(f"         file name's TC {metadata.tc_in_filename.tc}")
        return
