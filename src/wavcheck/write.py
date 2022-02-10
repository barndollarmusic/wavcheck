# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

from .data import Context
from .timecode import FrameRate


def write_framerate_file(ctx: Context, frame_rate: FrameRate):
    """Writes the chosen frame rate to FRAMERATE.txt in ctx.dir."""
    p = ctx.dir / "FRAMERATE.txt"
    with open(p, "w") as f:
        f.write(str(frame_rate))
