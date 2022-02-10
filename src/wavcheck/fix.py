# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

from .data import Context, InternalState


def maybe_fix_wav_files(ctx: Context, state: InternalState):
    """If applicable, prompts user to fix certain issues with WAV files."""
    # TODO: Implement.
