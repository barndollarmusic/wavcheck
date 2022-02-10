import sys

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
