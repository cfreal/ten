from colorama import Fore, Back, Style
from typing import Callable


COLOR_MAP = {
    "b": "BLUE",
    "g": "GREEN",
    "r": "RED",
    "y": "YELLOW",
    # b is already used by blue
    "x": "BLACK",
    "m": "MAGENTA",
    "c": "CYAN",
    "w": "WHITE",
}


def build_color(spec: str) -> Callable[[str], str]:
    """Converts a format specifier into a function that wraps text with ANSI
    code for colors.
    Format is at most 3 letters as follow:
        <lowercase letter> (foreground color)
        <uppercase letter> (background color)
        <symbols> (style)

    Foreground and background can be any of blue, red, etc.
    Style can be either empty or a `*`, indicating we want a bright color.
    Each of the three letter can be omitted.

    Example:

        ```
        # Returns red foreground, blue background, text in bright ANSI
        # escape sequence
        Colorized.build_color('rB*')('text in red with a blue background')
        # Neutral foreground, black background
        Colorized.build_color('-X')('text with black background')
        # Just yellow
        Colorized.build_color('y')('this gets written in yellow')
        ```
    """
    prefix = ""
    for c in spec or "":
        try:
            if c == "*":
                prefix += Style.BRIGHT
            elif c.islower():
                prefix += getattr(Fore, COLOR_MAP[c])
            elif c.isupper():
                prefix += getattr(Back, COLOR_MAP[c.lower()])
            else:
                raise KeyError
        except KeyError:
            raise ValueError(f"Invalid color format: {spec!r} ({c!r})")

    suffix = prefix and Style.RESET_ALL or ""

    def colorize(string: str) -> str:
        return prefix + string + suffix

    return colorize


bright = build_color("*")

red = build_color("r")
blue = build_color("b")
green = build_color("g")
magenta = build_color("m")
yellow = build_color("y")
white = build_color("w")
black = build_color("x")

back_red = build_color("R")
back_blue = build_color("B")
back_green = build_color("G")
back_magenta = build_color("M")
back_yellow = build_color("Y")
back_white = build_color("W")
back_black = build_color("X")
