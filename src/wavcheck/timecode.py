import enum
import math
import re

_MINS_PER_HR = 60
_SECS_PER_MIN = 60


@enum.unique
class FramesPerSec(str, enum.Enum):
    FPS_23_976 = "23.976"  # 23.976023976023976...
    FPS_24_000 = "24.000"
    FPS_25_000 = "25.000"
    FPS_29_970 = "29.970"  # 29.97002997002997...
    FPS_30_000 = "30.000"
    FPS_47_952 = "47.952"  # 47.952047952047952...
    FPS_48_000 = "48.000"
    FPS_50_000 = "50.000"
    FPS_59_940 = "59.940"  # 59.94005994005994...
    FPS_60_000 = "60.000"


class _FpsConfig:
    """Exact ratio configuration for a frames per second value."""
    frames: int
    per_wall_secs: int

    def __init__(self, frames: int, per_wall_secs: int):
        self.frames = frames
        self.per_wall_secs = per_wall_secs


_FRAME_RATES: dict[FramesPerSec, _FpsConfig] = {
    FramesPerSec.FPS_23_976: _FpsConfig(24000, 1001),  # 23.976023976023976...
    FramesPerSec.FPS_24_000: _FpsConfig(24, 1),
    FramesPerSec.FPS_25_000: _FpsConfig(25, 1),
    FramesPerSec.FPS_29_970: _FpsConfig(30000, 1001),  # 29.97002997002997...
    FramesPerSec.FPS_30_000: _FpsConfig(30, 1),
    FramesPerSec.FPS_47_952: _FpsConfig(48000, 1001),  # 47.952047952047952...
    FramesPerSec.FPS_48_000: _FpsConfig(48, 1),
    FramesPerSec.FPS_50_000: _FpsConfig(50, 1),
    FramesPerSec.FPS_59_940: _FpsConfig(60000, 1001),  # 59.94005994005994...
    FramesPerSec.FPS_60_000: _FpsConfig(60, 1),
}

_DROP_FRAMES_PER_10MINS: dict[FramesPerSec, int] = {
    FramesPerSec.FPS_29_970: 18,  # First 2 frames of minutes x1, x2, ..., x9.
    FramesPerSec.FPS_59_940: 36,  # First 4 frames of minutes x1, x2, ..., x9.
}


@enum.unique
class DropType(enum.Enum):
    NON_DROP = 1
    DROP = 2

    def __str__(self) -> str:
        if self == DropType.DROP:
            return "drop"
        else:
            return "non-drop"


class FrameRate:
    """A fully-specified framerate, with FPS and drop type."""
    _fps: FramesPerSec
    _drop_type: DropType

    def __init__(self, fps: FramesPerSec, drop_type: DropType):
        if drop_type == DropType.DROP and not fps in _DROP_FRAMES_PER_10MINS:
            raise Exception(
                f"[wavcheck] FramesPerSec {fps} is not a valid drop frame standard")

        self._fps = fps
        self._drop_type = drop_type

    def fps(self) -> FramesPerSec:
        return self._fps

    def drop_type(self) -> DropType:
        return self._drop_type

    def __str__(self) -> str:
        return f"{self._fps} {self._drop_type}"


_FPS_PATTERN = r"\d\d\.?\d?\d?\d?"
_NON_DROP_PATTERN = r"(?:non[-_\s]*drop|ndf?)"
_DROP_PATTERN = r"(?:drop|df?)"

# Groups: [1] FPS, [2] Drop Type.
_FRAMERATE_PATTERN = rf"({_FPS_PATTERN})\s*({_DROP_PATTERN}|{_NON_DROP_PATTERN})?"


@enum.unique
class FrameRateMatchLevel(enum.Enum):
    SEARCH_WITHIN = 1
    REQUIRE_FULL_MATCH = 2


def parse_framerate_within(s: str, level=FrameRateMatchLevel.SEARCH_WITHIN) -> FrameRate:
    """If s contains a valid framerate string, parses and returns it."""
    if level == FrameRateMatchLevel.SEARCH_WITHIN:
        match = re.search(_FRAMERATE_PATTERN, s, re.IGNORECASE)
    else:
        match = re.match(_FRAMERATE_PATTERN, s.strip(), re.IGNORECASE)
    if match is None:
        return None

    # Make sure framerate is valid.
    fps_str = match.group(1)

    fps_num = float(fps_str)
    if fps_str == "23.976" or fps_str == "23.98":
        fps = FramesPerSec.FPS_23_976
    elif fps_num == 24:
        fps = FramesPerSec.FPS_24_000
    elif fps_num == 25:
        fps = FramesPerSec.FPS_25_000
    elif fps_str == "29.970" or fps_str == "29.97":
        fps = FramesPerSec.FPS_29_970
    elif fps_num == 30:
        fps = FramesPerSec.FPS_30_000
    elif fps_str == "47.952" or fps_str == "47.95":
        fps = FramesPerSec.FPS_47_952
    elif fps_num == 48:
        fps = FramesPerSec.FPS_48_000
    elif fps_num == 50:
        fps = FramesPerSec.FPS_50_000
    elif fps_str == "59.940" or fps_str == "59.94":
        fps = FramesPerSec.FPS_59_940
    elif fps_num == 60:
        fps = FramesPerSec.FPS_60_000
    else:
        raise Exception(f"[wavcheck] Unsupported framerate fps: {fps_str}")

    # Warn user of potential ambiguity if applicable.
    fps_num_decimal_digits = max(len(fps_str) - 3, 0)  # Count after '##.'
    if (fps_num_decimal_digits == 0
            and (fps == FramesPerSec.FPS_24_000 or fps == FramesPerSec.FPS_30_000
                 or fps == FramesPerSec.FPS_48_000 or fps == FramesPerSec.FPS_60_000)):
        print()
        print((f"!! WARNING: frames per second {fps_str} is potentially ambiguous. "
               f"Specify as {fps} to avoid confusion."))
        print()

    drop_type_str = match.group(2) or ""
    drop_type = (DropType.DROP
                 if re.match(_DROP_PATTERN, drop_type_str, re.IGNORECASE)
                 else DropType.NON_DROP)

    # Reject 29.970 and 59.940 framerates that don't have an explicit drop or
    # non-drop qualifier.
    if (len(drop_type_str) == 0
            and (fps == FramesPerSec.FPS_29_970 or fps == FramesPerSec.FPS_59_940)):
        raise Exception(
            f"[wavcheck] frames per second {fps} ambiguous; specify drop or non-drop")

    return FrameRate(fps, drop_type)  # Checks combination for validity.


def wall_secs_to_durstr(wall_secs: float) -> str:
    """Converts time in wall seconds to human-readable duration string.

    Rounds fractional seconds to the nearest value (with 0.5 rounding up).
    Example output for 4994.5 seconds is "1h 23m 15s".
    """
    if not math.isfinite(wall_secs):
        raise Exception("wall_secs must be finite: " + wall_secs)

    is_negative = False
    if wall_secs < 0.0:
        wall_secs *= -1
        is_negative = True

    secs = math.floor(wall_secs + 0.5)  # Round 0.5 up.

    output = ""
    if is_negative and secs != 0:
        output += "(-) "

    hh = math.floor(secs / (_MINS_PER_HR * _SECS_PER_MIN))
    secs -= (_MINS_PER_HR * _SECS_PER_MIN) * hh

    mm = math.floor(secs / _SECS_PER_MIN)
    secs -= _SECS_PER_MIN * mm

    ss = secs

    # Output hh only if non-zero. No zero padding.
    if hh > 0:
        output += f"{hh}h "

    # Output mm only if non-zero. Zero pad if needed if there are hours.
    if hh > 0 or mm > 0:
        output += f"{mm:02}" if hh > 0 else str(mm)
        output += "m "

    # Always output ss. Zero pad if needed for 2 digits.
    output += f"{ss:02}"
    output += "s"

    return output
