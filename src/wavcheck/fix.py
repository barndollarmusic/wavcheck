# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import secrets

from .data import Context, CrossFileCheck, InternalState, WavFileState
from .prompt import prompt_should_fix_umids
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

    print("\n[wavcheck] DONE! Now all your WAV files can be their precious, unique selves. ❄️❄️❄️\n")


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

    print(f"OLD UMID: {umid.hex().upper()}")

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


def _maybe_add_tc_to_filenames(ctx: Context, state: InternalState):
    # TODO: Implement.
    pass
