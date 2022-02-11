<!--
SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.

SPDX-License-Identifier: Apache-2.0
-->

# wavcheck
Free little tool to checks audio WAV files in Broadcast Wave Format (BWF) for
issues (timecode, UMID, *etc.*). Designed especially for film &amp; TV composers
to use before sending out mix tracks or stems that need to remain synchronized.

Also can automatically add the BWF embedded starting timecode into filenames
(like `yourtune_TC01020304.wav`) and fix duplicate UMID problems.


<!-- TODO: Screenshot or GIF. -->


## How to Install

TODO: Document.


## How to Use

TODO: Document.


## Issues Checked

Looks for and warns about these potential problems:
- Non-standard WAV formats.
- Low bit depths (&lt; 16) or sample rates (&lt; 44.1k).
- Some files using different bit depths or sample rates than others.
- Very short audio files (&lt; 1s).
- Missing Broadcast Wave Format (BWF) metadata.
- Audio files that start at time `00:00:00:00`.
- Audio files that start at a fractional timecode frame position.
- Missing or duplicate SMPTE Unique Material Identifiers (UMIDs) within BWF metadata.
- Unnaturally loud BWF loudness stats (achievement unlocked&mdash;but please don't).
- Timecode in filename doesn't match BWF start time.


## Run into any problems (with this wavcheck tool)?

TODO: File an issue.
