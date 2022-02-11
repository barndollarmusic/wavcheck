# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import enum
import pathlib

from .timecode import FrameRate, Timecode

# The number of bits in a byte.
BITS_PER_BYTE = 8


class Context:
    """Contextual options and data used across this tool."""
    dir: pathlib.Path
    verbose: bool
    frame_rate: FrameRate

    def __init__(self, dir: pathlib.Path, verbose: bool):
        self.dir = dir
        self.verbose = verbose
        self.frame_rate = None  # Filled in later.


# Length of b"RIFF", <ChunkSize>, and b"WAVE" header.
WAV_HDR_LEN_BYTES = 12


@enum.unique
class SupportedFormatTag(enum.IntEnum):
    # The standard uncompressed PCM WAV format.
    WAVE_FORMAT_PCM = 0x0001

    # For MPEG-1 (audio only); technically supported by the BWF spec, but this
    # program will still warn about.
    WAVE_FORMAT_MPEG = 0x0050

    # NOTE: NOT technically BWF spec compliant unless used with the RF64 format
    # (which also allows for very large WAV files), but still common in
    # practice.
    WAVE_FORMAT_EXTENSIBLE = 0xFFFE


# Subtype for WAVE_FORMAT_EXTENSIBLE that corresponds to WAVE_FORMAT_PCM.
KSDATAFORMAT_SUBTYPE_PCM = bytes.fromhex("0100000000001000800000AA00389B71")


class FmtMetadata:
    """Holds basic WAV metadata from the fmt chunk."""
    # For all formats:
    format_tag: int
    num_chans: int
    bit_depth: int
    sample_rate_hz: int

    # For WAVE_FORMAT_EXTENSIBLE, the SubFormat GUID bytes.
    ext_sub_format: bytes

    def __init__(self):
        self.ext_sub_format = bytes()


class BwfMetadata:
    """Holds metadata read from BWF extension chunk in WAV file."""
    description: str
    originator: str
    originator_reference: str
    origination_date: str
    origination_time: str
    samples_since_origin: int
    version: int

    coding_history: str

    # For BWF Version 1+:
    umid: bytes  # 64 bytes.
    umid_hex: str

    # For BWF Version 2+:
    integrated_lufs: float
    loudness_range_lu: float
    max_dbtp: float
    max_momentary_lufs: float
    max_short_term_lufs: float


@enum.unique
class TcConfidence(enum.Enum):
    # Series of numbers interpreted as timecode, without explicit "TC" prefix.
    IMPLICIT_NUMBERS_ONLY = 0

    # Explcit "TC" prefix before series of numbers.
    EXPLICIT_TC_PREFIX = 1


class FilenameTimecode:
    """Timecode interpreted from a filename."""
    tc: Timecode
    confidence: TcConfidence

    def __init__(self, tc: Timecode, confidence: TcConfidence):
        self.tc = tc
        self.confidence = confidence


@enum.unique
class FilenameTcFormat(enum.Enum):
    # BASENAME TC01020304.wav:
    SPACE_NO_DOTS = 1

    # BASENAME_TC01020304.wav:
    UNDERSCORE_NO_DOTS = 2

    # BASENAME TC01.02.03.04.wav:
    SPACE_WITH_DOTS = 3

    # BASENAME_TC01.02.03.04.wav:
    UNDERSCORE_WITH_DOTS = 4

    def apply(self, filename: str, tc: Timecode) -> str:
        assert filename.endswith(".wav")
        new_name = filename.removesuffix(".wav")
        new_name += "_TC" if self._use_underscore() else " TC"
        new_name += str(tc).replace(":", "." if self._use_dots() else "")
        new_name += ".wav"
        return new_name

    def _use_underscore(self) -> bool:
        return (self == FilenameTcFormat.UNDERSCORE_NO_DOTS
                or self == FilenameTcFormat.UNDERSCORE_WITH_DOTS)

    def _use_dots(self) -> bool:
        return (self == FilenameTcFormat.SPACE_WITH_DOTS
                or self == FilenameTcFormat.UNDERSCORE_WITH_DOTS)


class WavMetadata:
    """Holds metadata read from a WAV file."""
    path: pathlib.Path

    # Basic fmt chunk metadata (required for a valid WAV):
    fmt_data: FmtMetadata

    # Broadcast Wave Format (BWF) metadata (None if missing):
    bwf_data: BwfMetadata

    # The number of audio bytes in the data chunk.
    data_size_bytes: int

    # Timecode parsed from the filename (e.g. some_prefix_TC01020304.wav).
    tc_in_filename: FilenameTimecode

    def __init__(self, path: pathlib.Path):
        self.path = path
        self.fmt_data = None
        self.bwf_data = None
        self.data_size_bytes = 0

    def duration_secs(self) -> float:
        """Returns duration of this WAV file in (fractional) seconds."""
        frame_size_bytes = self.fmt_data.num_chans * \
            (self.fmt_data.bit_depth / BITS_PER_BYTE)
        num_frames = self.data_size_bytes // frame_size_bytes
        return float(num_frames) / self.fmt_data.sample_rate_hz

    def bwf_start_time_secs(self, frame_rate: FrameRate) -> float:
        """Returns start time in (fractional) seconds from origin time."""
        assert self.bwf_data is not None  # Only call if present.

        start_samples = self.bwf_data.samples_since_origin
        return float(start_samples) / self.fmt_data.sample_rate_hz


@enum.unique
class WavFileCheck(enum.IntEnum):
    NONSTANDARD_FORMAT = 1
    LOW_BIT_DEPTH = 2
    LOW_SAMPLE_RATE = 3
    VERY_SHORT_DURATION = 4
    MISSING_BWF = 5
    STARTS_AT_TIME_ZERO = 6
    FRACTIONAL_FRAME_START_TC = 7
    MISSING_UMID = 8
    UNNATURALLY_LOUD = 9
    FILENAME_TC_MISMATCH = 10


@enum.unique
class CrossFileCheck(enum.IntEnum):
    MULTIPLE_BIT_DEPTHS = 1
    MULTIPLE_SAMPLE_RATES = 2
    NON_UNIQUE_UMIDS = 3


class WavFileState:
    """Maintains per-file state throughout each step in this program."""
    metadata: WavMetadata
    failed_checks: list[WavFileCheck]

    def __init__(self):
        self.failed_checks = []


class InternalState:
    """Internal state passed across each step of this checker."""
    wav_files: dict[str, WavFileState]
    failed_cross_checks: list[WavFileCheck]

    def __init__(self):
        self.wav_files = {}
        self.failed_cross_checks = []

    def warning_count(self):
        num_warnings = 0

        for filename in self.wav_files:
            num_warnings += len(self.wav_files[filename].failed_checks)
        num_warnings += len(self.failed_cross_checks)

        return num_warnings
