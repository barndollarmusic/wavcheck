# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import chunk
import os
import pathlib
import re
import struct
import sys

from .data import BwfMetadata, Context, FilenameTimecode, FmtMetadata, InternalState, SupportedFormatTag, TcConfidence, WavFileState, WavMetadata, WAV_HDR_LEN_BYTES
from .prompt import prompt_framerate, prompt_write_framerate_file
from .timecode import FrameRate, FrameRateMatchLevel, parse_framerate_within, parse_timecode_str
from .write import write_framerate_file


def read_or_prompt_framerate(ctx: Context, framerate_input: str) -> FrameRate:
    """Reads framerate input via argument, file, or prompts user for it."""
    # If user provided a -f, --framerate arg input, use it.
    if len(framerate_input) >= 1:
        return _read_framerate_from_arg_or_die(ctx, framerate_input)

    # If not, look for FRAMERATE.txt (or similarly named) within dir.
    frame_rate = _maybe_read_framerate_from_default_file(ctx)
    if frame_rate is not None:
        return frame_rate

    # Otherwise, ask the user to just tell us what the framerate is.
    frame_rate = prompt_framerate()

    # And see if they want to write their choice to FRAMERATE.txt.
    if prompt_write_framerate_file():
        write_framerate_file(ctx, frame_rate)

    return frame_rate


def _read_framerate_from_arg_or_die(ctx: Context, framerate_input: str) -> FrameRate:
    """Tries to read framerate from provided arg, or exits with failure."""
    # See if argument directly specified a framerate:
    frame_rate = parse_framerate_within(
        framerate_input, FrameRateMatchLevel.REQUIRE_FULL_MATCH)
    if frame_rate is not None:
        return frame_rate

    # Otherwise, see if this argument names a file.
    # If relative, interpret relative to dir.
    path = pathlib.Path(framerate_input)
    path = path if path.is_absolute() else ctx.dir.joinpath(path)
    path = path.resolve()
    if not path.exists() or not path.is_file():
        sys.exit((f"[wavcheck] ERROR: Trying to find a framerate in {path}, "
                  "but it doesn't exist as a file"))

    return _read_framerate_from_file_or_die(path)


_FRAMERATE_LABEL_PATTERN = r"frame[-_\s]*rate"


def _maybe_read_framerate_from_default_file(ctx: Context) -> FrameRate:
    """Tries to read framerate from FRAMERATE.txt or similar in ctx.dir."""
    candidate_file: pathlib.Path = None
    with os.scandir(ctx.dir) as entries:
        for entry in entries:
            if entry.is_file() and re.search(_FRAMERATE_LABEL_PATTERN, str(entry.name), re.IGNORECASE):
                candidate_file = pathlib.Path(entry.path)
                break
    if candidate_file is None:
        return None

    return _read_framerate_from_file_or_die(candidate_file)


def _read_framerate_from_file_or_die(file: pathlib.Path):
    """Reads framerate from file (name or contents), or exits with failure."""
    print(f"[wavcheck] Looking for a framerate within {file} ...")

    # See if framerate is directly contained in the filename.
    try:
        frame_rate = parse_framerate_within(file.name)
        if frame_rate is not None:
            return frame_rate
    except Exception:
        pass

    # Search file contents.
    with open(file, "r") as f:
        # Look for a line of form "Framerate: <framerate>" (or similar).
        for line in f:
            match = re.search(_FRAMERATE_LABEL_PATTERN, line, re.IGNORECASE)
            if match:
                frame_rate = parse_framerate_within(line)
                break

        # Otherwise, see if entire file contents match.
        if frame_rate is None:
            f.seek(0)
            frame_rate = parse_framerate_within(f.read(),
                                                FrameRateMatchLevel.REQUIRE_FULL_MATCH)

    if frame_rate is None:
        sys.exit(f"[wavcheck] Unable to find valid framerate in {file}")
    return frame_rate


def read_wav_files(ctx: Context) -> InternalState:
    """Reads metadata for all WAV files in the given dir."""
    print(f"[wavcheck] Reading .wav files in '{ctx.dir}' ...")

    result = InternalState()
    with os.scandir(ctx.dir) as entries:
        for entry in entries:
            if entry.is_file() and str(entry.name).endswith(".wav"):
                if ctx.verbose:
                    print(f"[wavcheck] Reading {entry.name} ...")
                p = pathlib.Path(entry.path).resolve()
                result.wav_files[p.name] = WavFileState()
                result.wav_files[p.name].metadata = _read_wav_file(p)

    _clean_up_filename_tcs(result)
    return result


def _read_wav_file(path: pathlib.Path) -> WavMetadata:
    """Reads metadata for the given WAV file."""
    metadata = WavMetadata(path)
    metadata.tc_in_filename = _find_tc_in_filename(path.name)

    with open(path, mode="rb") as file:
        # Read all relevant RIFF chunk metadata.
        file.seek(WAV_HDR_LEN_BYTES)
        while True:
            try:
                subchunk = chunk.Chunk(file, bigendian=False)
                if subchunk.getname() == b"fmt ":
                    metadata.fmt_data = _read_fmt_metadata(subchunk)
                if subchunk.getname() == b"bext":
                    metadata.bwf_data = _read_bwf_metadata(subchunk)
                if subchunk.getname() == b"data":
                    # TODO: Support RF64 long WAV files.
                    metadata.data_size_bytes = subchunk.getsize()
                subchunk.skip()  # Advance file to next subchunk.
            except EOFError:
                break

    return metadata


_TC_NUMBERS_NO_SEPARATORS = r"\d?\d\d\d\d\d\d\d"
_TC_NUMBERS_SEPARATORS = r"\d?\d[-_. ]\d\d[-_. ]\d\d[-_. ]\d\d"
_TC_NUMBERS_FILENAME_PATTERN = rf"(?:{_TC_NUMBERS_NO_SEPARATORS}|{_TC_NUMBERS_SEPARATORS})"
_TC_EXPLICIT_FILENAME_PATTERN = re.compile(
    rf"TC[-_. ]*({_TC_NUMBERS_FILENAME_PATTERN})[^\d]", re.IGNORECASE)
_TC_IMPLICIT_FILENAME_PATTERN = re.compile(
    rf"[^\d]({_TC_NUMBERS_FILENAME_PATTERN})[^\d]")


def _find_tc_in_filename(name: str) -> FilenameTimecode:
    """Returns a Timecode if found in a known pattern within name."""
    # Prefer explicit match with TC prefix.
    match = _TC_EXPLICIT_FILENAME_PATTERN.search(name)
    if match:
        return FilenameTimecode(parse_timecode_str(match.group(1)),
                                TcConfidence.EXPLICIT_TC_PREFIX)

    # Otherwise, look for the last matching sequence of 7-8 digits.
    last_match = None
    for last_match in _TC_IMPLICIT_FILENAME_PATTERN.finditer(name):
        continue
    if last_match:
        return FilenameTimecode(parse_timecode_str(last_match.group(1)),
                                TcConfidence.IMPLICIT_NUMBERS_ONLY)

    return None  # No timecode found.


_FMT_STRUCT_PACK_FMT = (
    "<"      # Little endian.

    # Common Fields:
    "H"      # [0] FormatTag (uint16)
    "H"      # [1] NumChannels (uint16)
    "I"      # [2] SamplesPerSec (uint32)
    "I"      # [3] AvgBytesPerSec (uint32)
    "H"      # [4] BlockAlign (uint16)

    # At leats valid for WAVE_FORMAT_PCM:
    "H"      # [5] BitsPerSample (uint16)
)


_FMT_EXTENSIBLE_PACK_FMT = (
    "<"      # Little endian.
    "H"      # [0] ExtraBytes (uint16)
    "H"      # [1] ValidBitsPerSample (uint16)
    "I"      # [2] ChannelMask (uint32)
    "16s"    # [3] SubFormat GUID (byte[16])
)


def _read_fmt_metadata(fmt_chunk: chunk.Chunk) -> FmtMetadata:
    """Populates fmt metadata."""
    fmt_data = fmt_chunk.read()

    common_field_size = struct.calcsize(_FMT_STRUCT_PACK_FMT)
    fmt_fields = struct.unpack(
        _FMT_STRUCT_PACK_FMT, fmt_data[:common_field_size])

    result = FmtMetadata()
    result.format_tag = fmt_fields[0]
    result.num_chans = fmt_fields[1]
    result.bit_depth = fmt_fields[5]
    result.sample_rate_hz = fmt_fields[2]

    # For WAVE_FORMAT_EXTENSIBLE, read the extra fields.
    if result.format_tag == SupportedFormatTag.WAVE_FORMAT_EXTENSIBLE:
        ext_field_size = struct.calcsize(_FMT_EXTENSIBLE_PACK_FMT)
        ext_field_end = common_field_size + ext_field_size
        ext_fields = struct.unpack(
            _FMT_EXTENSIBLE_PACK_FMT, fmt_data[common_field_size:ext_field_end])

        result.bit_depth = ext_fields[1]  # May reduce actual bits per sample.
        result.ext_sub_format = ext_fields[3]

    return result


_BWF_STRUCT_PACK_FMT = (
    "<"      # Little endian.

    # For BWF Version 0+:
    "256s"   # [0] Descsription (char[256])
    "32s"    # [1] Originator (char[32])
    "32s"    # [2] OriginatorReference (char[32])
    "10s"    # [3] OriginationDate (char[10])
    "8s"     # [4] OriginationTime (char[8])
    "Q"      # [5] TimeReference (uint64)
    "H"      # [6] Version (uint16)

    # For BWF Version 1+:
    "64s"    # [7] UMID (byte[64])

    # For BWF Version 2+:
    "h"      # [8] LoudnessValue
    "h"      # [9] LoudnessRange
    "h"      # [10] MaxTruePeakLevel
    "h"      # [11] MaxMomentaryLoudness
    "h"      # [12] MaxShortTermLoudness

    # Reserved space for future versions:
    "180s"

    # Coding history follows, but it is a variable-length CRLF-terminated string.
)


def _read_bwf_metadata(bwf_chunk: chunk.Chunk) -> BwfMetadata:
    """Populates BWF metadata."""
    bwf_data = bwf_chunk.read()

    coding_history_offset = struct.calcsize(_BWF_STRUCT_PACK_FMT)
    bwf_fields = struct.unpack(
        _BWF_STRUCT_PACK_FMT, bwf_data[:coding_history_offset])

    result = BwfMetadata()
    result.description = _safe_str(bwf_fields[0])
    result.originator = _safe_str(bwf_fields[1])
    result.originator_reference = _safe_str(bwf_fields[2])
    result.origination_date = _safe_str(bwf_fields[3])
    result.origination_time = _safe_str(bwf_fields[4])
    result.samples_since_origin = bwf_fields[5]
    result.version = bwf_fields[6]

    if result.version >= 1:
        result.umid = bwf_fields[7]
        result.umid_hex = result.umid.hex().upper()

    if result.version >= 2:
        result.integrated_lufs = float(bwf_fields[8]) / 100.0
        result.loudness_range_lu = float(bwf_fields[9]) / 100.0
        result.max_dbtp = float(bwf_fields[10]) / 100.0
        result.max_momentary_lufs = float(bwf_fields[11]) / 100.0
        result.max_short_term_lufs = float(bwf_fields[12]) / 100.0

    result.coding_history = _safe_str(
        bwf_data[coding_history_offset:]).rstrip("\r\n")
    return result


def _safe_str(data: bytes) -> str:
    last_nonzero_pos = 0
    for idx in reversed(range(len(data))):
        if data[idx] != 0:
            last_nonzero_pos = idx
            break

    # Interpret as ISO-8859-1 for a more forgiving ASCII.
    raw_str = data[:last_nonzero_pos + 1].decode("iso-8859-1").rstrip("\0")

    # But escape non-printable characters.
    return raw_str.encode("unicode_escape").decode("iso-8859-1")


def _clean_up_filename_tcs(state: InternalState):
    found_any_explicit = False

    for filename in state.wav_files:
        filename_tc = state.wav_files[filename].metadata.tc_in_filename
        if (filename_tc is not None
                and filename_tc.confidence == TcConfidence.EXPLICIT_TC_PREFIX):
            found_any_explicit = True
            break

    # If any explicit TC-prefixed timecodes were detected in filenames, ignore
    # any implicit digit sequences that weren't TC prefixed.
    if found_any_explicit:
        for filename in state.wav_files:
            filename_tc = state.wav_files[filename].metadata.tc_in_filename
            if (filename_tc is not None
                    and filename_tc.confidence == TcConfidence.IMPLICIT_NUMBERS_ONLY):
                # Clear.
                state.wav_files[filename].metadata.tc_in_filename = None
