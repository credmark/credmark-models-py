from sys import platform
from typing import Optional


class TermColors:
    _PREF = "\033["
    _FAINT = "2m"
    _UNDERLINE = "4m"
    _INVERT = "7m"
    _RESET = "0m"

    BLACK = "30m"
    RED = "31m"
    GREEN = "32m"
    YELLOW = "33m"
    BLUE = "34m"
    MAGENTA = "35m"
    CYAN = "36m"
    WHITE = "37m"

    BG_BLACK = "40m"
    BG_RED = "41m"
    BG_GREEN = "42m"
    BG_YELLOW = "43m"
    BG_BLUE = "44m"
    BG_MAGENTA = "45m"
    BG_CYAN = "46m"
    BG_WHITE = "47m"

    @staticmethod
    def apply(text: str,
              color: Optional[str] = None,
              bg_color: Optional[str] = None,
              faint=False,
              underline=False,
              invert=False):

        if platform == 'win32':
            return text
        else:
            highlighted_text = ""
            if bg_color is not None:
                highlighted_text += f"{TermColors._PREF}{bg_color}"

            if color is not None:
                highlighted_text += f"{TermColors._PREF}{color}"

            if faint is True:
                highlighted_text += f"{TermColors._PREF}{TermColors._FAINT}"

            if underline is True:
                highlighted_text += f"{TermColors._PREF}{TermColors._UNDERLINE}"

            if invert is True:
                highlighted_text += f"{TermColors._PREF}{TermColors._INVERT}"

            highlighted_text += text
            highlighted_text += f"{TermColors._PREF}{TermColors._RESET}"
            return highlighted_text
