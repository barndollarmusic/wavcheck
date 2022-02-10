import base64
import chunk
import os
import pathlib
import struct
import wave

from .data import BwfMetadata
from .data import InternalState
from .data import WavMetadata
from .data import WavFileState

_BITS_PER_BYTE = 8

# Length of b"RIFF", <ChunkSize>, and b"WAVE" header.
_WAV_HDR_LEN_BYTES = 12


def read_wav_files(dir: pathlib.Path) -> InternalState:
    """Reads metadata for all WAV files in the given dir."""
    print("[wavcheck] Reading .wav files in '%s' ..." % dir)

    result = InternalState()
    with os.scandir(dir) as entries:
        for entry in entries:
            if entry.is_file() and str(entry.name).endswith(".wav"):
                p = pathlib.Path(entry.path).resolve()
                result.wav_files[p.name] = WavFileState()
                result.wav_files[p.name].metadata = _read_wav_file(p)
    return result


def _read_wav_file(path: pathlib.Path) -> WavMetadata:
    """Reads metadata for the given WAV file."""

    metadata = WavMetadata(path)

    with open(path, mode='rb') as file:
        # TODO: Make sure Python's wave library can handle surround WAV formats.
        # Read basic WAV file format metadata.
        with wave.open(file, mode='rb') as wave_file:
            metadata.num_chans = wave_file.getnchannels()
            metadata.bit_depth = _BITS_PER_BYTE * wave_file.getsampwidth()
            metadata.sample_rate_hz = wave_file.getframerate()
            metadata.duration_secs = float(
                wave_file.getnframes()) / wave_file.getframerate()

        # Read Broadcast Wave Format (BWF) chunk metadata, if present.
        file.seek(_WAV_HDR_LEN_BYTES)
        while True:
            try:
                subchunk = chunk.Chunk(file, bigendian=False)
                if subchunk.getname() == b"bext":
                    metadata.bwf_data = _read_bwf_metadata(subchunk)
                subchunk.skip()  # Advance file to next subchunk.
            except EOFError:
                break

    return metadata


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
    result.description = _ascii_str(bwf_fields[0])
    result.originator = _ascii_str(bwf_fields[1])
    result.originator_reference = _ascii_str(bwf_fields[2])
    result.origination_date = _ascii_str(bwf_fields[3])
    result.origination_time = _ascii_str(bwf_fields[4])
    result.samples_since_origin = bwf_fields[5]
    result.version = bwf_fields[6]

    if result.version >= 1:
        result.umid = bwf_fields[7]
        result.umid_base64 = base64.standard_b64encode(
            result.umid).decode("ascii")

    if result.version >= 2:
        result.integrated_lufs = float(bwf_fields[8]) / 100.0
        result.loudness_range_lu = float(bwf_fields[9]) / 100.0
        result.max_dbtp = float(bwf_fields[10]) / 100.0
        result.max_momentary_lufs = float(bwf_fields[11]) / 100.0
        result.max_short_term_lufs = float(bwf_fields[12]) / 100.0

    result.coding_history = _ascii_str(
        bwf_data[coding_history_offset:]).rstrip("\r\n")
    return result


def _ascii_str(data: bytes) -> str:
    return data.decode("ascii").rstrip("\0")
