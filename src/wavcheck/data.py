import enum
import pathlib


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


class WavMetadata:
    """Holds metadata read from a WAV file."""
    path: pathlib.Path

    # Basic WAV format metadata:
    num_chans: int
    bit_depth: int
    sample_rate_hz: int
    duration_secs: float

    # Broadcast Wave Format (BWF) metadata (None if missing):
    bwf_data: BwfMetadata

    def __init__(self, path: pathlib.Path):
        self.path = path
        self.bwf_data = None


@enum.unique
class WavFileCheck(enum.Enum):
    LOW_BIT_DEPTH = 1
    LOW_SAMPLE_RATE = 2
    VERY_SHORT_DURATION = 3
    MISSING_BWF = 4
    STARTS_AT_TIME_ZERO = 5
    MISSING_UMID = 6
    UNNATURALLY_LOUD = 7


@enum.unique
class CrossFileCheck(enum.Enum):
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
