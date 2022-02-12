# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import chunk

from .data import Context, WavFileState, WAV_HDR_LEN_BYTES
from .print import print_error_exit, print_info
from .timecode import FrameRate


def write_framerate_file(ctx: Context, frame_rate: FrameRate):
    """Writes the chosen frame rate to FRAMERATE.txt in ctx.dir."""
    p = ctx.dir / "FRAMERATE.txt"
    with open(p, "w") as f:
        f.write(str(frame_rate))


# The number of bytes after start of
_BWF_UMID_OFFSET = 348

# Length of UMID in bytes.
_BWF_UMID_LEN = 64


def write_new_umid(wav_file: WavFileState, new_umid: bytearray):
    """Writes new_umid to the given wav_file."""
    assert len(new_umid) == _BWF_UMID_LEN

    print_info(f"Updating UMID for {wav_file.metadata.path.name} ...")
    with open(wav_file.metadata.path, "r+b") as file:
        file.seek(WAV_HDR_LEN_BYTES)
        subchunk: chunk.Chunk = None

        # Seek to the BWF chunk.
        while True:
            try:
                subchunk = chunk.Chunk(file, bigendian=False)
                if subchunk.getname() == b"bext":
                    break  # Found it.
                subchunk.skip()  # Advance file to next subchunk.
            except EOFError:
                break

        if subchunk is None:
            print_error_exit(
                f"BWF chunk not found in {wav_file.metadata.path}, "
                "was it changed on disk in the middle of running this program?")

        # Sanity check that this chunk is big enough, so we never write data
        # into another chunk if somehow the BWF chunk was corrput.
        assert subchunk.getsize() >= _BWF_UMID_OFFSET + _BWF_UMID_LEN

        # Advance to the UMID field.
        subchunk.seek(_BWF_UMID_OFFSET)
        umid_pos = file.tell()

        # For sanity, verify that these bytes match the old UMID we read previously.
        reread_umid = file.read(_BWF_UMID_LEN)
        if wav_file.metadata.bwf_data.umid != reread_umid:
            print_error_exit(
                f"{wav_file.metadata.path}: "
                f"UMID re-read {reread_umid.hex().upper()} does not match "
                f"previously read value {wav_file.metadata.bwf_data.umid.hex().upper()}")

        # Write the new UMID value.
        file.seek(umid_pos)
        num_written = file.write(new_umid)
        assert num_written == len(new_umid)
