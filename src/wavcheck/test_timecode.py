# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import unittest

from .timecode import FrameRate, Timecode, parse_framerate_within, wall_secs_to_durstr, wall_secs_to_tc_left


def _fr(s: str) -> FrameRate:
    frame_rate = parse_framerate_within(s)
    assert frame_rate is not None
    return frame_rate


class TestWallSecsToDurStr(unittest.TestCase):
    def test_works_for_positive_durations(self):
        self.assertEqual(wall_secs_to_durstr(0), "00s")
        self.assertEqual(wall_secs_to_durstr(0.49999999), "00s")
        self.assertEqual(wall_secs_to_durstr(0.5), "01s")

        self.assertEqual(wall_secs_to_durstr(59.49999999), "59s")
        self.assertEqual(wall_secs_to_durstr(59.5), "1m 00s")

        self.assertEqual(wall_secs_to_durstr(3540), "59m 00s")
        self.assertEqual(wall_secs_to_durstr(3599.49999999), "59m 59s")
        self.assertEqual(wall_secs_to_durstr(3600), "1h 00m 00s")
        self.assertEqual(wall_secs_to_durstr(3765), "1h 02m 45s")

        self.assertEqual(wall_secs_to_durstr(359999.49999999), "99h 59m 59s")
        self.assertEqual(wall_secs_to_durstr(359999.98333333), "100h 00m 00s")

    def test_works_for_negative_durations(self):
        self.assertEqual(wall_secs_to_durstr(-0.0), "00s")
        self.assertEqual(wall_secs_to_durstr(-0.49999999), "00s")
        self.assertEqual(wall_secs_to_durstr(-0.5), "(-) 01s")

        self.assertEqual(wall_secs_to_durstr(-59.49999999), "(-) 59s")

        self.assertEqual(wall_secs_to_durstr(-3540), "(-) 59m 00s")

        self.assertEqual(wall_secs_to_durstr(-3765), "(-) 1h 02m 45s")


class TimecodeTestCase(unittest.TestCase):
    def assert_tc(self, tc: Timecode, expected: str):
        self.assertEqual(str(tc), expected)


class TestWallSecsToTcLeft(TimecodeTestCase):
    def test_works(self):
        self.assert_tc(wall_secs_to_tc_left(
            1.04, _fr("50.00 non-drop")), "00:00:01:02")

        self.assert_tc(wall_secs_to_tc_left(
            60.02663333, _fr("29.97 drop")), "00:00:59:28")
        self.assert_tc(wall_secs_to_tc_left(
            60.02663334, _fr("29.97 drop")), "00:00:59:29")
        self.assert_tc(wall_secs_to_tc_left(
            60.06, _fr("29.97 drop")), "00:01:00:02")

        # 44:33:22:11 => 160,402 timecode seconds plus 11 frames:

        self.assert_tc(wall_secs_to_tc_left(160562.86079167,
                       _fr("23.976 non-drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(160562.86079167,
                       _fr("23.98 non-drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(160402.45833334,
                       _fr("24.000 non-drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(160402.45833334,
                       _fr("24.00 non-drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(
            160402.44, _fr("25.000 non-drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(
            160402.44, _fr("25.00 non-drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(160562.76903334,
                       _fr("29.970 non-drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(160562.76903334,
                       _fr("29.97 non-drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(160402.36666667,
                       _fr("30.000 non-drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(160402.36666667,
                       _fr("30.00 non-drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(160562.63139584,
                       _fr("47.952 non-drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(160562.63139584,
                       _fr("47.95 non-drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(160402.22916667,
                       _fr("48.000 non-drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(160402.22916667,
                       _fr("48.00 non-drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(
            160402.22, _fr("50.000 non-drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(
            160402.22, _fr("50.00 non-drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(160562.58551667,
                       _fr("59.940 non-drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(160562.58551667,
                       _fr("59.94 non-drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(160402.18333334,
                       _fr("60.000 non-drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(160402.18333334,
                       _fr("60.00 non-drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(
            160402.20863334, _fr("29.970 drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(
            160402.20863334, _fr("29.97 drop")), "44:33:22:11")

        self.assert_tc(wall_secs_to_tc_left(
            160402.02511667, _fr("59.940 drop")), "44:33:22:11")
        self.assert_tc(wall_secs_to_tc_left(
            160402.02511667, _fr("59.94 drop")), "44:33:22:11")


if __name__ == "__main__":
    unittest.main()
