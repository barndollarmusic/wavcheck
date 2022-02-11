<!--
SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.

SPDX-License-Identifier: Apache-2.0
-->

# wavcheck
Free little command-line tool to check audio WAV files in Broadcast Wave Format
(BWF) for issues (timecode, UMID, *etc.*). Designed especially for film &amp; TV
composers to use before sending out mix tracks or stems that need to remain
precisely synchronized.

Also can automatically add the BWF embedded starting timecode into filenames
(like `yourtune_TC01020304.wav`) and fix duplicate UMID problems (which can
cause warnings when importing into Pro Tools, for example).


<!-- TODO: Screenshot or GIF. -->


## How to Install

**PREREQUISITE**: requires Python 3.6 or later installed on your system. You can
download the latest verion [here](https://www.python.org/downloads/). See
[Requirements for Installing
Packages](https://packaging.python.org/en/latest/tutorials/installing-packages/#requirements-for-installing-packages)
if you need more help.

Open a terminal program (Terminal, PowerShell, Command Prompt, *etc.*) and
install **wavcheck** with these commands (you may need to restart your terminal
after `ensurepath`):
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
pipx install wavcheck
```

For Windows users, Python 3 might be installed as the `py` program:
```cmd
py -m pip install --user pipx
py -m pipx ensurepath
pipx install wavcheck
```

### Upgrading to a New Version

```bash
pipx upgrade wavcheck
```


## Quick Start

Put all the `.wav` files you want to check in the same directory and change to
it. Then just run `wavcheck`:

```bash
cd path/to/your/audio/dir
wavcheck
```

It will ask you to choose a frame rate, report any warnings, and offer to
automatically fix certain problems if possible.

To print more verbose output, including all the Broadcast Wave Format (BWF)
embedded metadata for every WAV file, add `-v` or `--verbose`:

```bash
wavcheck --verbose
```

To print out help information with a complete list of possible command-line
arguments:

```bash
wavcheck -h
```


## Issues Checked

Warns about these potential problems:
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


## Automatically Reading Framerate

When you first run `wavcheck` and choose a frame rate, it will ask if you want
to write that choice into a file called `FRAMERATE.txt` in the same directory.
Then on any subsequent runs, it will read the frame rate from that file. (I
recommend including this file along with your audio files to avoid any
confusion, since BWF metadata does NOT encode the frame rate standard in any
way).

Alternatively, you can put the framerate directly in the file name, like
`FRAMERATE 24.000 non-drop.txt`.

Or if you have another existing file where you already have your frame rate
written, you can use it instead. For example, you could have a file called
`_IMPORTANT INFO.txt`:

```
Picture Version: XYZ_2022-02-22
Frame Rate: 29.970 drop
Anything else you want...
```

Then tell `wavcheck` to find the framerate within that file:

```bash
wavcheck --framerate="_IMPORTANT INFO.txt"
```


## Run into any problems (with this wavcheck tool)?

Look for an existing bug report or file a new issue
[here](https://github.com/barndollarmusic/wavcheck/issues).
