import builtins
import re
from enum import IntEnum, auto, Enum
from keyword import iskeyword
from typing import NamedTuple

from PyQt6.Qsci import QsciLexerCustom, QsciScintilla
from PyQt6.QtGui import QColor, QFont
from ptyx.context import GLOBAL_CONTEXT


def get_all_tags() -> dict[str, tuple[int, int, list[str] | None]]:
    from ptyx.syntax_tree import SyntaxTreeGenerator
    from ptyx_mcq import extend_compiler

    tags = SyntaxTreeGenerator.tags.copy()
    tags |= extend_compiler()["tags"]
    return tags


TAGS = set(get_all_tags())

PYTHON_BUILTINS = set(vars(builtins))
PTYX_BUILTINS = set(GLOBAL_CONTEXT)
ALL_BUILTINS = PYTHON_BUILTINS | PTYX_BUILTINS


class Style(IntEnum):
    DEFAULT = 0
    PTYX_TAG = auto()
    PTYX_VARIABLE = auto()
    PTYX_EXPRESSION = auto()
    PTYX_COMMENT = auto()
    PYTHON_BLOCK = auto()
    PYTHON_INT = auto()
    PYTHON_STR = auto()
    PYTHON_KEYWORD = auto()
    PYTHON_BUILTIN = auto()
    PYTHON_COMMENT = auto()
    MCQ_CORRECT_ANSWER = auto()
    MCQ_INCORRECT_ANSWER = auto()
    MCQ_NEUTRALIZED_ANSWER = auto()


class Mode(Enum):
    DEFAULT = auto()
    PYTHON = auto()
    EXPRESSION = auto()


class StyleInfo(NamedTuple):
    mode: Mode
    text_color: str
    paper_color: str
    is_bold: bool
    is_italic: bool


STYLES_LIST: dict[Style, StyleInfo] = {
    Style.DEFAULT: StyleInfo(Mode.DEFAULT, "#000000", "#ffffff", False, False),  # default
    Style.PTYX_TAG: StyleInfo(Mode.DEFAULT, "#ffb230", "#ffffff", False, False),  # ptyx tag
    Style.PTYX_VARIABLE: StyleInfo(Mode.DEFAULT, "#776599", "#ffffff", False, False),  # ptyx variable
    Style.PTYX_EXPRESSION: StyleInfo(Mode.EXPRESSION, "#000000", "#fcf5bb", False, False),  # ptyx expression
    Style.PTYX_COMMENT: StyleInfo(Mode.DEFAULT, "#cccccc", "#ffffff", False, True),  # ptyx comment
    Style.PYTHON_BLOCK: StyleInfo(Mode.PYTHON, "#000000", "#fffad1", False, False),  # python block
    Style.PYTHON_INT: StyleInfo(Mode.PYTHON, "#0000bf", "#fffad1", False, False),  # python int
    Style.PYTHON_STR: StyleInfo(Mode.PYTHON, "#007f00", "#fffad1", False, False),  # python str
    Style.PYTHON_KEYWORD: StyleInfo(Mode.PYTHON, "#ffb230", "#fffad1", True, False),  # python keyword
    Style.PYTHON_BUILTIN: StyleInfo(Mode.PYTHON, "#ffb230", "#fffad1", False, False),  # python func
    Style.PYTHON_COMMENT: StyleInfo(Mode.PYTHON, "#cccccc", "#fffad1", True, False),  # python comment
    Style.MCQ_CORRECT_ANSWER: StyleInfo(Mode.DEFAULT, "#000000", "#d7ffd1", False, False),  # correct answer
    Style.MCQ_INCORRECT_ANSWER: StyleInfo(
        Mode.DEFAULT, "#000000", "#fffad1", False, False
    ),  # incorrect answer
    Style.MCQ_NEUTRALIZED_ANSWER: StyleInfo(
        Mode.DEFAULT, "#000000", "#ebebeb", False, False
    ),  # neutralized answer
}

# self.setColor(QColor("#ff000000"), 0)  # default: black
# self.setColor(QColor("#ffb230"), 1)  # ptyx tag: orange
# self.setColor(QColor("#776599"), 2)  # ptyx variable: violet gris
# self.setColor(QColor("#cccccc"), 3)  # ptyx comment: gray
# self.setColor(QColor("#ff007f00"), 4)  # python block: green
# self.setColor(QColor("#0000bf"), 5)  # python int: blue
# self.setColor(QColor("#ff007f00"), 6)  # python str: green
# self.setColor(QColor("#ff007f00"), 7)  # python func: green
# self.setColor(QColor("#ff007f00"), 8)  # correct answer: green
# self.setColor(QColor("#ff007f00"), 9)  # incorrect answer: green


class MyLexer(QsciLexerCustom):
    def __init__(self, parent):
        super().__init__(parent)
        # Default text settings
        # ----------------------
        self.setDefaultColor(QColor("#ff000000"))
        self.setDefaultPaper(QColor("#ffffffff"))
        self.setDefaultFont(QFont("Consolas", 14))

        for style, (_, text_color, paper_color, is_bold, is_italic) in STYLES_LIST.items():
            self.setColor(QColor(text_color), style)
            self.setPaper(QColor(paper_color), style)
            self.setFont(
                QFont(
                    "Consolas",
                    14,
                    weight=(QFont.Weight.Bold if is_bold else QFont.Weight.Normal),
                    italic=is_italic,
                ),
                style,
            )

    def language(self):
        return "PTYX MCQ"

    def description(self, style: int) -> str:
        if style < len(Style):
            return Style(style).name
        return ""

    def styleText(self, start: int, end: int):
        editor = self.parent()
        assert isinstance(editor, QsciScintilla)
        # 1. Initialize the styling procedure
        # ------------------------------------
        self.startStyling(start)

        # 2. Slice out a part from the text
        # ----------------------------------
        text = editor.text()[start:end]

        # 3. Tokenize the text
        # ---------------------
        # Test in https://regex101.com/
        p = re.compile(r"\.{4,}\n|#\w+|#\{|^[-+!] |\s+|\w+\d*|\.\d+|\d+\.?|\W", flags=re.MULTILINE)

        # 'token_list' is a list of tuples: (token_name, token_len)
        token_list: list[tuple[str, int]] = [
            (token, len(bytearray(token, "utf-8"))) for token in p.findall(text)
        ]

        # 4. Style the text
        # ------------------
        # 4.1 Get previous mode if any.
        if start > 0:
            previous_style = editor.SendScintilla(editor.SCI_GETSTYLEAT, start - 1)
            mode = STYLES_LIST[previous_style].mode
        else:
            mode = Mode.DEFAULT
        # 4.2 Style the text in a loop
        for i, (token, length) in enumerate(token_list):
            assert isinstance(token, str) and isinstance(length, int), (token, length)
            if token.startswith("...."):
                self.setStyling(length, Style.PYTHON_BLOCK)
                assert token.rstrip("\n").rstrip(".") == "", token
                mode = Mode.PYTHON if mode == Mode.DEFAULT else Mode.DEFAULT
            elif token == "#PYTHON":
                self.setStyling(length, Style.PYTHON_BLOCK)
                mode = mode.PYTHON
            elif token == "#END_PYTHON" or (token == "#END" and mode == Mode.PYTHON):
                self.setStyling(length, Style.PYTHON_BLOCK)
                mode = mode.DEFAULT
            elif mode == Mode.PYTHON:
                if iskeyword(token):
                    self.setStyling(length, Style.PYTHON_KEYWORD)
                elif token in ALL_BUILTINS:
                    self.setStyling(length, Style.PYTHON_BUILTIN)
                elif token.strip(".").isdigit():
                    self.setStyling(length, Style.PYTHON_INT)
                else:
                    self.setStyling(length, Style.PYTHON_BLOCK)
            elif mode == Mode.EXPRESSION:
                if token == "}":
                    mode = mode.DEFAULT
                    self.setStyling(length, Style.PTYX_TAG)
                else:
                    self.setStyling(length, Style.PTYX_EXPRESSION)
            else:
                # print(repr(token))
                if token.startswith("#"):
                    if token in TAGS:
                        self.setStyling(length, Style.PTYX_TAG)
                    elif token == "#{":
                        mode = Mode.EXPRESSION
                        self.setStyling(length, Style.PTYX_TAG)
                    elif token.startswith("#") and token[1:].isalpha():
                        self.setStyling(length, Style.PTYX_VARIABLE)
                    else:
                        self.setStyling(length, Style.DEFAULT)
                elif token == "- ":
                    self.setStyling(length, Style.MCQ_INCORRECT_ANSWER)
                elif token == "+ ":
                    self.setStyling(length, Style.MCQ_CORRECT_ANSWER)
                elif token == "! ":
                    self.setStyling(length, Style.MCQ_NEUTRALIZED_ANSWER)
                else:
                    # Default style
                    self.setStyling(length, Style.DEFAULT)
