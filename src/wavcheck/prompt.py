# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import sys

from wavcheck.data import FilenameTcFormat

from .timecode import DropType, FrameRate, FramesPerSec


def prompt_framerate() -> FrameRate:
    """Interactively prompts user to select a framerate."""
    print()
    print("[ 1] 23.976 non-drop    [ 7] 47.952 non-drop")
    print("[ 2] 24.000 non-drop    [ 8] 48.000 non-drop")
    print("[ 3] 25.000 non-drop    [ 9] 50.000 non-drop")
    print("[ 4] 29.970 drop        [10] 59.940 drop")
    print("[ 5] 29.970 non-drop    [11] 59.940 non-drop")
    print("[ 6] 30.000 non-drop    [12] 60.000 non-drop")
    print()

    try:
        choice = int(input(">>>>>>>>>> Select your framerate (1-12): "))
        if choice < 1 or 12 < choice:
            raise Exception()
    except Exception:
        sys.exit("[wavcheck] ERROR: Invalid framerate input")

    if choice == 1:
        return FrameRate(FramesPerSec.FPS_23_976, DropType.NON_DROP)
    elif choice == 2:
        return FrameRate(FramesPerSec.FPS_24_000, DropType.NON_DROP)
    elif choice == 3:
        return FrameRate(FramesPerSec.FPS_25_000, DropType.NON_DROP)
    elif choice == 4:
        return FrameRate(FramesPerSec.FPS_29_970, DropType.DROP)
    elif choice == 5:
        return FrameRate(FramesPerSec.FPS_29_970, DropType.NON_DROP)
    elif choice == 6:
        return FrameRate(FramesPerSec.FPS_30_000, DropType.NON_DROP)
    elif choice == 7:
        return FrameRate(FramesPerSec.FPS_47_952, DropType.NON_DROP)
    elif choice == 8:
        return FrameRate(FramesPerSec.FPS_48_000, DropType.NON_DROP)
    elif choice == 9:
        return FrameRate(FramesPerSec.FPS_50_000, DropType.NON_DROP)
    elif choice == 10:
        return FrameRate(FramesPerSec.FPS_59_940, DropType.DROP)
    elif choice == 11:
        return FrameRate(FramesPerSec.FPS_59_940, DropType.NON_DROP)
    else:
        return FrameRate(FramesPerSec.FPS_60_000, DropType.NON_DROP)


def prompt_write_framerate_file() -> bool:
    """Asks user if they want to write a FRAMERATE.txt file."""
    print(">>>>>>>>>> 📎 So I don't have to ask next time, would you like me to")
    answer = input("              write that to a FRAMERATE.txt file? [y/N] ")
    return answer.strip().lower().startswith("y")


def prompt_should_fix_umids() -> bool:
    """Asks user if they want to make all UMIDs unique."""
    print(">>>>>>>>>> 📎 Looks like you have non-unique UMIDs, would you like me to")
    answer = input("              fix them to all be unique? [y/N] ")
    return answer.strip().lower().startswith("y")


def prompt_should_append_filename_tcs() -> bool:
    """Asks user if they want to append any missing timecodes to filenames."""
    print(">>>>>>>>>> 📎 Looks like some filenames don't contain timecodes,")
    answer = input(
        "              would you like me to rename those files for you? [y/N] ")
    return answer.strip().lower().startswith("y")


def prompt_filename_suffix_format() -> FilenameTcFormat:
    """Interactively prompts user to select a filename timecode format."""
    print()
    print("How should a file BASENAME.wav starting at 01:02:03:04 be renamed?\n")
    print("[1] BASENAME TC01020304.wav")
    print("[2] BASENAME_TC01020304.wav")
    print("[3] BASENAME TC01.02.03.04.wav")
    print("[4] BASENAME_TC01.02.03.04.wav")
    print()

    try:
        choice = int(
            input(">>>>>>>>>> Select a filename timecode suffix format (1-4): "))
        if choice < 1 or 4 < choice:
            raise Exception()
    except Exception:
        sys.exit(
            "[wavcheck] ERROR: Invalid filename timecode suffix format choice")

    if choice == 1:
        return FilenameTcFormat.SPACE_NO_DOTS
    elif choice == 2:
        return FilenameTcFormat.UNDERSCORE_NO_DOTS
    elif choice == 3:
        return FilenameTcFormat.SPACE_WITH_DOTS
    else:
        return FilenameTcFormat.UNDERSCORE_WITH_DOTS
