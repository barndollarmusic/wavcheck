# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

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

    def int_fps(self) -> int:
        rate_info = _FRAME_RATES[self._fps]
        return math.ceil(float(rate_info.frames) / rate_info.per_wall_secs)

    def drop_type(self) -> DropType:
        return self._drop_type

    def drop_frames_per_10mins(self) -> int:
        if self._drop_type == DropType.NON_DROP:
            return 0
        return _DROP_FRAMES_PER_10MINS[self._fps]

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


class Timecode:
    """Numerical timecode value with HH:MM:SS:FF."""
    hh: int
    mm: int
    ss: int
    ff: int

    def __init__(self, hh: int, mm: int, ss: int, ff: int):
        # Note: Validation happens elsewhere.
        self.hh = hh
        self.mm = mm
        self.ss = ss
        self.ff = ff

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timecode):
            return False
        other_tc: Timecode = other
        return (self.hh == other_tc.hh
                and self.mm == other_tc.mm
                and self.ss == other_tc.ss
                and self.ff == other_tc.ff)

    def __str__(self) -> str:
        return f"{self.hh:02}:{self.mm:02}:{self.ss:02}:{self.ff:02}"


_NON_DIGIT_PATTERN = re.compile(r"[^\d]")


def parse_timecode_str(s: str) -> Timecode:
    """Parses a timecode from all the numeric digits in s."""
    digits = _NON_DIGIT_PATTERN.sub("", s)  # Remove non-digits.
    digits = f"{int(digits):08}"  # Zero pad to 8 digits.
    if len(digits) != 8:
        raise Exception(f"[wavcheck] Invalid timecode pattern '{s}'")

    hh = int(digits[0:2])
    mm = int(digits[2:4])
    ss = int(digits[4:6])
    ff = int(digits[6:8])
    return Timecode(hh, mm, ss, ff)


def _frames_per_dropped_block(fr: FrameRate) -> int:
    # A block of frames is dropped from the first second (SS=00) of 9 out of
    # every 10 minutes. For 29.97 fps, for example, there are 18 frames dropped
    # per 10 minutes, in blocks of 2 frames at a time.
    return fr.drop_frames_per_10mins() // 9


def tc_to_wall_secs(tc: Timecode, fr: FrameRate) -> float:
    """Returns timecode as (fractional) wall time in seconds from origin."""
    frame_idx = _tc_to_frame_idx(tc, fr)
    return _frame_idx_to_wall_secs(frame_idx, fr)


def _tc_to_frame_idx(tc: Timecode, fr: FrameRate) -> int:
    # Calculate first ignoring dropped frames.
    tc_total_mins = (_MINS_PER_HR * tc.hh) + tc.mm
    tc_total_secs = (_SECS_PER_MIN * tc_total_mins) + tc.ss
    frame_idx = (fr.int_fps() * tc_total_secs) + tc.ff

    # Adjust for any frame numbers that were dropped.
    if fr.drop_frames_per_10mins() > 0:
        # Frames dropped through start of HH:
        frames_dropped_per_hr = 6 * fr.drop_frames_per_10mins()
        frame_idx -= tc.hh * frames_dropped_per_hr

        # Frames dropped from start of HH to start of this 10 minute block:
        frame_idx -= (math.floor(float(tc.mm) / 10)
                      * fr.drop_frames_per_10mins())

        # Frames dropped since start of this 10 minute block:
        frame_idx -= (tc.mm % 10) * _frames_per_dropped_block(fr)

    return frame_idx


def _frame_idx_to_wall_secs(frame_idx: int, fr: FrameRate) -> float:
    rate_info = _FRAME_RATES[fr.fps()]
    return frame_idx * rate_info.per_wall_secs / float(rate_info.frames)


def wall_secs_to_tc_left(wall_secs: float, fr: FrameRate) -> Timecode:
    """Returns timecode of closest frame before or exactly equal to given wall_secs."""
    fractional_frame_idx = wall_secs_to_fractional_frame_idx(wall_secs, fr)
    frame_idx = math.floor(fractional_frame_idx)
    return _frame_idx_to_tc(frame_idx, fr)


def wall_secs_to_fractional_frame_idx(wall_secs: float, fr: FrameRate) -> float:
    """Returns (fractional) frame index of wall_secs from origin."""
    rate_info = _FRAME_RATES[fr.fps()]
    return wall_secs * rate_info.frames / rate_info.per_wall_secs


def _frame_idx_to_tc(frame_idx: int, fr: FrameRate) -> Timecode:
    if frame_idx < 0:
        raise Exception("Negative frame indexes are not supported")

    frames_per_min = fr.int_fps() * _SECS_PER_MIN
    frames_per_hr = frames_per_min * _MINS_PER_HR

    # If this is a drop frame standard, adjust for any dropped frames.
    frames_remaining = frame_idx + \
        _frames_dropped_before_frame_idx(frame_idx, fr)

    hh = math.floor(float(frames_remaining) / frames_per_hr)
    frames_remaining -= hh * frames_per_hr

    mm = math.floor(float(frames_remaining) / frames_per_min)
    frames_remaining -= mm * frames_per_min

    ss = math.floor(float(frames_remaining) / fr.int_fps())
    frames_remaining -= ss * fr.int_fps()

    ff = frames_remaining
    return Timecode(hh, mm, ss, ff)


def _frames_dropped_before_frame_idx(frame_idx: int, fr: FrameRate) -> int:
    if fr.drop_type() == DropType.NON_DROP:
        return 0

    frames_per_non_drop_min = fr.int_fps() * _SECS_PER_MIN
    frames_per_dropped_block = _frames_per_dropped_block(fr)
    frames_per_drop_min = frames_per_non_drop_min - frames_per_dropped_block

    # Count # of full blocks of 10 minutes (of timecode, not wall time).
    frames_per_10mins = 10 * frames_per_non_drop_min - fr.drop_frames_per_10mins()

    frames_remaining = frame_idx
    num_complete_10min_blocks = math.floor(
        float(frames_remaining) / frames_per_10mins)
    frames_remaining -= frames_per_10mins * num_complete_10min_blocks

    num_dropped_frames = num_complete_10min_blocks * fr.drop_frames_per_10mins()

    if frames_remaining >= frames_per_non_drop_min:
        # First minute of this 10 minute block has no dropped frames.
        frames_remaining -= frames_per_non_drop_min

        # Each complete drop minute plus the current minute drops one block of frames.
        num_complete_drop_mins = math.floor(
            float(frames_remaining) / frames_per_drop_min)
        num_dropped_frames += (num_complete_drop_mins +
                               1) * frames_per_dropped_block

    return num_dropped_frames
