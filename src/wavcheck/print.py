# SPDX-FileCopyrightText: 2022 Barndollar Music, Ltd.
#
# SPDX-License-Identifier: Apache-2.0

import sys
import colorama


def print_init():
    """Initializes console printing (for color support)."""
    colorama.init()


def _bright(color: str, text: str) -> str:
    return f"{colorama.Style.BRIGHT}{color}{text}{colorama.Style.RESET_ALL}"


def _reg(color: str, text: str) -> str:
    return f"{color}{text}{colorama.Style.RESET_ALL}"


def _dim(text: str) -> str:
    return f"{colorama.Style.DIM}{text}{colorama.Style.RESET_ALL}"


class Phrases:
    WAVCHECK_PREFIX = _dim("[wavcheck]")
    DONE = _bright(colorama.Fore.GREEN, "DONE")
    ERROR = _bright(colorama.Fore.RED, "ERROR")
    SUCCESS = _bright(colorama.Fore.GREEN, "SUCCESS")
    WARNING = _bright(colorama.Fore.YELLOW, "WARNING")


def print_error_exit(err_msg: str):
    """Prints err_msg and exits with failure status code."""
    print(f"{Phrases.WAVCHECK_PREFIX} {Phrases.ERROR}: {err_msg}\n")
    sys.exit(1)


def print_success_exit(msg: str):
    """Prints msg and exists with success status code."""
    print(f"\n{Phrases.WAVCHECK_PREFIX} {Phrases.SUCCESS}: {msg}")
    sys.exit(0)


def print_check_warning(warn_msg: str):
    """Prints warn_msg with a bold warning prefix."""
    print(f"{_reg(colorama.Fore.YELLOW, '!!')} {Phrases.WARNING}: {warn_msg}")


def stern_warning(warn_msg: str) -> str:
    """Wraps warn_msg so that it prints in red."""
    return _reg(colorama.Fore.RED, warn_msg)


def print_stern_warning(warn_msg: str):
    """Prints warn_msg in red, but without a warning prefix."""
    print(f"{Phrases.WAVCHECK_PREFIX} {stern_warning(warn_msg)}")


def light_warning(warn_msg: str) -> str:
    """Returns warn_msg in yellow."""
    return _reg(colorama.Fore.YELLOW, warn_msg)


def print_light_warning(warn_msg: str):
    """Prints warn_msg in yellow, but without a warning prefix."""
    print(f"{Phrases.WAVCHECK_PREFIX} {light_warning(warn_msg)}")


def print_bold(text: str):
    """Prints text in bold (bright)."""
    print(f"{_bright('', text)}")


def print_info(info_msg: str):
    """Prints a regular importance info_msg."""
    print(f"{Phrases.WAVCHECK_PREFIX} {info_msg}")


def print_verbose(verbose_msg: str):
    """Prints a lower importance verbose_msg."""
    print(f"{Phrases.WAVCHECK_PREFIX} {_dim(verbose_msg)}")


def print_blank_line():
    """Prints a blank line."""
    print()


_PROMPT_PREFIX = _reg(colorama.Fore.MAGENTA, ">>>>>>>>>>")
_PROMPT_INDENT = "          "

_CLIPPY_PREFIX = "📎"
_CLIPPY_INDENT = "  "


def input_prompt(prompt: str) -> str:
    """Inputs a user choice with given prompt text."""
    return input(f"{_PROMPT_PREFIX} {_reg(colorama.Fore.MAGENTA, prompt)}")


def prompt_indented(text: str) -> str:
    return f"{_PROMPT_INDENT} {_reg(colorama.Fore.MAGENTA, text)}"


def print_clippy(text: str):
    print(f"{_PROMPT_PREFIX} {_CLIPPY_PREFIX} {_reg(colorama.Fore.MAGENTA, text)}")


def clippy_indented(text: str) -> str:
    """Indents text to the same column as a clippy prompt."""
    return f"{_PROMPT_INDENT} {_CLIPPY_INDENT} {_reg(colorama.Fore.MAGENTA, text)}"


def print_clippy_indented(text: str):
    """Prints indented to the same column as a clippy prompt."""
    print(clippy_indented(text))


def print_banner(heading: str, color: str = ""):
    """Prints heading with a prominent bold banner."""
    print_blank_line()
    print_bold(
        f"{color}================================================================================")
    print_bold(f"{color}{heading}")
    print_bold(
        f"{color}================================================================================")
    print_blank_line()


def print_ind2(text: str):
    """Prints text indented by 2 spaces."""
    print(f"  {text}")


def print_ind4(text: str):
    """Prints text indented by 4 spaces."""
    print(f"    {text}")


def blue_field(field_name: str) -> str:
    """Returns field_name so it prints in blue."""
    return _reg(colorama.Fore.BLUE, field_name)


def cyan_field(field_name: str) -> str:
    """Returns field_name so it prints in cyan."""
    return _reg(colorama.Fore.CYAN, field_name)
