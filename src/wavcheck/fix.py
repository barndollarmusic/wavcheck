# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import enum
import collections
import os
import secrets

from .data import Context, CrossFileCheck, InternalState, TcConfidence, WavFileCheck, WavFileState
from .prompt import prompt_filename_suffix_format, prompt_should_append_filename_tcs, prompt_should_fix_umids
from .timecode import wall_secs_to_tc_left
from .write import write_new_umid


def maybe_fix_wav_files(ctx: Context, state: InternalState):
    """If applicable, prompts user to fix certain issues with WAV files."""
    _maybe_fix_umids(ctx, state)
    _maybe_add_tc_to_filenames(ctx, state)


def _maybe_fix_umids(ctx: Context, state: InternalState):
    if CrossFileCheck.NON_UNIQUE_UMIDS not in state.failed_cross_checks:
        return

    print()
    if not prompt_should_fix_umids():
        return

    seen_hex_umids: set[str] = set()
    for filename in state.wav_files:
        wav_file = state.wav_files[filename]
        if wav_file.metadata.bwf_data is not None:
            hex_umid = wav_file.metadata.bwf_data.umid_hex
            if hex_umid in seen_hex_umids:
                # Non-unique! Fix this file.
                hex_umid = _fix_umid(wav_file, seen_hex_umids)

            seen_hex_umids.add(hex_umid)

    print(("\n[wavcheck] DONE! Now all your WAV files can be their precious, "
           "unique selves. ❄️ ❄️ ❄️\n"))


def _fix_umid(wav_file: WavFileState, seen_hex_umids: set[str]) -> str:
    umid = bytearray(wav_file.metadata.bwf_data.umid)
    assert len(umid) == 64

    # Basic UMID bytes (first 32 bytes):
    # [12] Universal Label
    # [1] L
    # [3] Instance Number
    # [16] Material Number

    # Extended UMID bytes (last 32 bytes):
    # [8] Time/Date
    # [12] Spatial Coordinates
    # [4] Country
    # [4] Org
    # [4] User

    # Fix UMID by randomly generating a new Material Number.
    while True:
        umid[13:16] = b"\x00\x00\x00"  # Instance Number 0.
        umid[16:32] = secrets.token_bytes(16)

        new_umid_hex = umid.hex().upper()
        if new_umid_hex not in seen_hex_umids:
            break

    # Write this back to the WAV file.
    write_new_umid(wav_file, umid)
    return new_umid_hex


@enum.unique
class TcFilenameStatus(enum.Enum):
    NONE_NO_BWF_START_TIME = 0
    NONE_WITH_BWF_START_TIME = 1
    IMPLICIT_MISMATCH = 2
    IMPLICIT_MATCH = 3
    EXPLICIT_MISMATCH = 4
    EXPLICIT_MATCH = 5

    def is_potentially_fixable(self) -> bool:
        return (self == TcFilenameStatus.NONE_WITH_BWF_START_TIME
                or self == TcFilenameStatus.IMPLICIT_MISMATCH)


def _tc_filename_status(wav_file: WavFileState) -> TcFilenameStatus:
    has_bwf_start_time = (wav_file.metadata.bwf_data
                          and wav_file.metadata.bwf_data.samples_since_origin != 0)
    has_mismatch = WavFileCheck.FILENAME_TC_MISMATCH in wav_file.failed_checks

    tc_in_filename = wav_file.metadata.tc_in_filename
    if tc_in_filename is None:
        return (TcFilenameStatus.NONE_WITH_BWF_START_TIME if has_bwf_start_time
                else TcFilenameStatus.NONE_NO_BWF_START_TIME)

    if tc_in_filename.confidence == TcConfidence.IMPLICIT_NUMBERS_ONLY:
        return (TcFilenameStatus.IMPLICIT_MISMATCH if has_mismatch
                else TcFilenameStatus.IMPLICIT_MATCH)
    else:
        return (TcFilenameStatus.EXPLICIT_MISMATCH if has_mismatch
                else TcFilenameStatus.EXPLICIT_MATCH)


def _maybe_add_tc_to_filenames(ctx: Context, state: InternalState):
    statuses: dict[str, TcFilenameStatus] = {}
    status_counts = collections.Counter()

    # First take stock of what types of filename timecodes were present.
    num_fixable = 0
    has_fractional_frame_errors = False
    for filename in state.wav_files:
        wav_file = state.wav_files[filename]
        status = _tc_filename_status(wav_file)
        if status.is_potentially_fixable():
            num_fixable += 1
        statuses[filename] = status
        status_counts[status] += 1
        if WavFileCheck.FRACTIONAL_FRAME_START_TC in wav_file.failed_checks:
            has_fractional_frame_errors = True

    # If there's nothing to automatically fix, bail out.
    if num_fixable == 0:
        return

    # If there were any explicit mismatches or a mixture of implicit matches +
    # mismatches, the user should fix the existing filenames first.
    if (status_counts[TcFilenameStatus.EXPLICIT_MISMATCH] >= 1
        or (status_counts[TcFilenameStatus.IMPLICIT_MISMATCH] >= 1
            and status_counts[TcFilenameStatus.IMPLICIT_MATCH] >= 1)):
        print("[wavcheck] Please fix existing filenames with timecode mismatches.")
        return

    print()

    # If there were only implicit mismatches, these may not have been
    # interpreted correctly (less confident without explicit "TC" prefix).
    if status_counts[TcFilenameStatus.IMPLICIT_MISMATCH] >= 1:
        print("              (note potential existing filename timecode problems)")

    # If there were fractional frame start times, the user also may not want to
    # rename with these timecodes.
    if has_fractional_frame_errors:
        print("              (note fractional frame start time warnings)")

    # Ask user whether to rename fixable files and in what format.
    if not prompt_should_append_filename_tcs():
        return
    format = prompt_filename_suffix_format()

    # Rename those files.
    for filename in state.wav_files:
        status = statuses[filename]
        if not status.is_potentially_fixable():
            continue

        wav_file = state.wav_files[filename]
        start_secs = wav_file.metadata.bwf_start_time_secs(ctx.frame_rate)
        start_tc = wall_secs_to_tc_left(start_secs, ctx.frame_rate)

        new_name = format.apply(filename, start_tc)
        print(f"[wavcheck] Renaming to {new_name} ...")

        new_path = wav_file.metadata.path.parent / new_name
        os.rename(wav_file.metadata.path, new_path)
