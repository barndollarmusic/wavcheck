import math

_MINS_PER_HR = 60
_SECS_PER_MIN = 60


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
        output += hh
        output += "h "
    
    # Output mm only if non-zero. Zero pad if needed if there are hours.
    if hh > 0 or mm > 0:
        output += f"{mm:02}" if hh > 0 else str(mm)
        output += "m "
    
    # Always output ss. Zero pad if needed for 2 digits.
    output += f"{ss:02}"
    output += "s"

    return output
