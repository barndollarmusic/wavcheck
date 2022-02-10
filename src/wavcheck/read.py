import chunk
import os
import pathlib
import struct

from .data import BwfMetadata, FmtMetadata, InternalState, SupportedFormatTag, WavFileState, WavMetadata


# Length of b"RIFF", <ChunkSize>, and b"WAVE" header.
_WAV_HDR_LEN_BYTES = 12


def read_wav_files(dir: pathlib.Path, verbose: bool) -> InternalState:
    """Reads metadata for all WAV files in the given dir."""
    print("[wavcheck] Reading .wav files in '%s' ..." % dir)

    result = InternalState()
    with os.scandir(dir) as entries:
        for entry in entries:
            if entry.is_file() and str(entry.name).endswith(".wav"):
                if verbose:
                    print(f"[wavcheck] Reading {entry.name} ...")
                p = pathlib.Path(entry.path).resolve()
                result.wav_files[p.name] = WavFileState()
                result.wav_files[p.name].metadata = _read_wav_file(p)
    return result


def _read_wav_file(path: pathlib.Path) -> WavMetadata:
    """Reads metadata for the given WAV file."""

    metadata = WavMetadata(path)

    with open(path, mode='rb') as file:
        # Read Broadcast Wave Format (BWF) chunk metadata, if present.
        file.seek(_WAV_HDR_LEN_BYTES)
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
