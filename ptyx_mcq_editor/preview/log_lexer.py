import re
from enum import IntEnum, auto
from typing import TYPE_CHECKING

from PyQt6.Qsci import QsciLexerCustom, QsciScintilla
from PyQt6.QtGui import QColor, QFont

if TYPE_CHECKING:
    from ptyx_mcq_editor.preview.log_viewer import LogViewer


class Style(IntEnum):
    HIDDEN = 0

    DEFAULT = auto()
    BLACK = auto()
    DARK_GRAY = auto()
    RED = auto()
    LIGHT_RED = auto()
    GREEN = auto()
    LIGHT_GREEN = auto()
    BROWN_ORANGE = auto()
    YELLOW = auto()
    BLUE = auto()
    LIGHT_BLUE = auto()
    PURPLE = auto()
    LIGHT_PURPLE = auto()
    CYAN = auto()
    LIGHT_CYAN = auto()
    LIGHT_GRAY = auto()
    WHITE = auto()


codes = {
    "0": Style.DEFAULT,
    "0;30": Style.BLACK,
    "1;30": Style.DARK_GRAY,
    "0;31": Style.RED,
    "1;31": Style.LIGHT_RED,
    "0;32": Style.GREEN,
    "1;32": Style.LIGHT_GREEN,
    "0;33": Style.BROWN_ORANGE,
    "1;33": Style.YELLOW,
    "0;34": Style.BLUE,
    "1;34": Style.LIGHT_BLUE,
    "0;35": Style.PURPLE,
    "1;35": Style.LIGHT_PURPLE,
    "0;36": Style.CYAN,
    "1;36": Style.LIGHT_CYAN,
    "0;37": Style.LIGHT_GRAY,
    "1;37": Style.WHITE,
}

colors = {
    Style.DEFAULT: "#000000",
    Style.BLACK: "#000000",
    Style.DARK_GRAY: "#555555",
    Style.RED: "#FF0000",
    Style.LIGHT_RED: "#FF5555",
    Style.GREEN: "#00FF00",
    Style.LIGHT_GREEN: "#55FF55",
    Style.BROWN_ORANGE: "#FFAA00",
    Style.YELLOW: "#dfbf39",
    Style.BLUE: "#0000FF",
    Style.LIGHT_BLUE: "#5555FF",
    Style.PURPLE: "#FF00FF",
    Style.LIGHT_PURPLE: "#FF55FF",
    Style.CYAN: "#26c4ec",
    Style.LIGHT_CYAN: "#50abc2",
    Style.LIGHT_GRAY: "#AAAAAA",
    Style.WHITE: "#FFFFFF",
}


# Test in https://regex101.com/
TOKENS_REGEX = re.compile(
    "|".join(
        [
            "\033\\[[0-9;]+m",  # change display
            "[^\033]+",
        ]
    ),
    flags=re.MULTILINE,
)


class LogLexer(QsciLexerCustom):
    def __init__(self, parent):
        super().__init__(parent)
        # Default text settings
        # ----------------------
        self.setDefaultColor(QColor("#ff000000"))
        self.setDefaultPaper(QColor("#ffffffff"))
        self.setDefaultFont(QFont("Consolas", 13))
        self.parent().SendScintilla(QsciScintilla.SCI_STYLESETVISIBLE, Style.HIDDEN, False)

        for style, hex_color in colors.items():
            # self.SCI_STYLESETVISIBLE()
            self.setColor(QColor(hex_color), style)
            # self.setPaper(QColor(paper_color), style)
            self.setFont(
                QFont(
                    "Consolas",
                    13,
                    # (QFont.Weight.Bold if is_bold else QFont.Weight.Normal),
                    # is_italic,
                ),
                style,
            )
            # self.setEolFill(fill_line, style)

    def language(self):
        return "ptyx log"

    def description(self, style: int) -> str:
        if style < len(Style):
            return Style(style).name
        return ""

    def styleText(self, start: int, end: int):
        editor: LogViewer = self.parent()  # type: ignore
        assert isinstance(editor, QsciScintilla)
        # 1. Initialize the styling procedure
        # ------------------------------------
        self.startStyling(start)

        # 2. Slice out a part from the text
        # ----------------------------------
        text = editor.text(start, end)
        # print(repr(text))
        # 3. Tokenize the text
        # ---------------------

        # 'token_list' is a list of tuples: (token_name, token_len)
        token_list: list[str] = TOKENS_REGEX.findall(text)

        # 4. Style the text
        # ------------------
        # 4.1 Get previous style and mode if any.
        if start > 0:
            style = Style(editor.SendScintilla(editor.SCI_GETSTYLEAT, start - 1))
        else:
            style = Style.DEFAULT
        # 4.2 Style the text in a loop
        for i, token in enumerate(token_list):
            assert isinstance(token, str), token
            if token.startswith("\033[") and token.endswith("m"):
                code = token[2:-1]
                if code != "0" and ";" not in code:
                    code = "0;" + code
                try:
                    style = codes[code]
                except KeyError:
                    pass
                self.setStyling(len(bytearray(token, "utf-8")), Style.HIDDEN)
            else:
                # In setStyling, the length is the number of bytes, not the number of unicode characters !
                self.setStyling(len(bytearray(token, "utf-8")), style)
