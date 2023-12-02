import builtins
import re
from enum import IntEnum, auto, Enum
from keyword import iskeyword
from typing import NamedTuple, TYPE_CHECKING

from PyQt6.Qsci import QsciLexerCustom, QsciScintilla
from PyQt6.QtGui import QColor, QFont
from ptyx.context import GLOBAL_CONTEXT

if TYPE_CHECKING:
    from ptyx_mcq_editor.editor.editor_widget import EditorWidget


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
    PTYX_LATEX_MACRO = auto()

    PYTHON_BLOCK = auto()
    PYTHON_BLOCK_DELIMITER = auto()
    PYTHON_INT = auto()
    PYTHON_STR = auto()
    PYTHON_KEYWORD = auto()
    PYTHON_BUILTIN = auto()
    PYTHON_COMMENT = auto()

    PYTHON_SINGLE_QUOTE_STRING = auto()
    PYTHON_DOUBLE_QUOTE_STRING = auto()
    PYTHON_TRIPLE_DOUBLE_QUOTE_STRING = auto()
    PYTHON_TRIPLE_SINGLE_QUOTE_STRING = auto()
    PYTHON_UNCLOSED_STRING = auto()

    MCQ_CORRECT_ANSWER = auto()
    MCQ_INCORRECT_ANSWER = auto()
    MCQ_NEUTRALIZED_ANSWER = auto()
    MCQ_OR = auto()


QUOTES = {
    Style.PYTHON_SINGLE_QUOTE_STRING: "'",
    Style.PYTHON_DOUBLE_QUOTE_STRING: '"',
    Style.PYTHON_TRIPLE_SINGLE_QUOTE_STRING: "'''",
    Style.PYTHON_TRIPLE_DOUBLE_QUOTE_STRING: '"""',
}

REVERSED_QUOTES = {val: key for key, val in QUOTES.items()}


class Mode(Enum):
    DEFAULT = auto()
    PYTHON = auto()
    PYTHON_STRING = auto()
    EXPRESSION = auto()


class StyleInfo(NamedTuple):
    mode: Mode
    text_color: str
    paper_color: str
    is_bold: bool
    is_italic: bool
    fill_line: bool


STYLES_LIST: dict[Style, StyleInfo] = {
    # pTyX styles
    Style.DEFAULT: StyleInfo(Mode.DEFAULT, "#000000", "#ffffff", False, False, False),
    Style.PTYX_TAG: StyleInfo(Mode.DEFAULT, "#ffb230", "#ffffff", False, False, False),
    Style.PTYX_VARIABLE: StyleInfo(Mode.DEFAULT, "#776599", "#ffffff", False, False, False),
    Style.PTYX_LATEX_MACRO: StyleInfo(Mode.DEFAULT, "#753527", "#ffffff", False, False, False),
    Style.PTYX_COMMENT: StyleInfo(Mode.DEFAULT, "#cccccc", "#ffffff", False, True, False),
    # Expressions (small inline snippets of python code inside pTyX code)
    Style.PTYX_EXPRESSION: StyleInfo(Mode.EXPRESSION, "#000000", "#fcf5bb", False, False, False),
    # Python code
    Style.PYTHON_BLOCK: StyleInfo(Mode.PYTHON, "#000000", "#fcf9d9", False, False, True),
    Style.PYTHON_BLOCK_DELIMITER: StyleInfo(Mode.PYTHON, "#000000", "#faf4b6", False, False, True),
    Style.PYTHON_INT: StyleInfo(Mode.PYTHON, "#0000bf", "#fffad1", False, False, False),
    Style.PYTHON_STR: StyleInfo(Mode.PYTHON, "#007f00", "#fffad1", False, False, False),
    Style.PYTHON_KEYWORD: StyleInfo(Mode.PYTHON, "#ffb230", "#fffad1", True, False, False),
    Style.PYTHON_BUILTIN: StyleInfo(Mode.PYTHON, "#cc12ff", "#fffad1", False, False, False),
    Style.PYTHON_COMMENT: StyleInfo(Mode.PYTHON, "#cccccc", "#fffad1", True, False, False),
    # Python strings
    Style.PYTHON_SINGLE_QUOTE_STRING: StyleInfo(Mode.PYTHON_STRING, "#43b064", "#fffad1", False, False, True),
    Style.PYTHON_DOUBLE_QUOTE_STRING: StyleInfo(Mode.PYTHON_STRING, "#43b064", "#fffad1", False, False, True),
    Style.PYTHON_TRIPLE_DOUBLE_QUOTE_STRING: StyleInfo(
        Mode.PYTHON_STRING, "#43b064", "#fffad1", False, False, True
    ),
    Style.PYTHON_TRIPLE_SINGLE_QUOTE_STRING: StyleInfo(
        Mode.PYTHON_STRING, "#43b064", "#ffd7d1", False, False, True
    ),
    # Special style for unclosed strings. Mode must be set to PYTHON, and not PYTHON_STRING!
    Style.PYTHON_UNCLOSED_STRING: StyleInfo(Mode.PYTHON, "#43b064", "#ffa1a1", False, False, True),
    # MCQ specific syntax
    Style.MCQ_CORRECT_ANSWER: StyleInfo(Mode.DEFAULT, "#138f00", "#d7ffd1", False, False, True),
    Style.MCQ_INCORRECT_ANSWER: StyleInfo(Mode.DEFAULT, "#ab1600", "#ffd7d1", False, False, True),
    Style.MCQ_NEUTRALIZED_ANSWER: StyleInfo(Mode.DEFAULT, "#707070", "#c2c2c2", False, False, True),
    Style.MCQ_OR: StyleInfo(Mode.DEFAULT, "#4c66fc", "#ffebc7", False, False, True),
}


class MyLexer(QsciLexerCustom):
    def __init__(self, parent):
        super().__init__(parent)
        # Default text settings
        # ----------------------
        self.setDefaultColor(QColor("#ff000000"))
        self.setDefaultPaper(QColor("#ffffffff"))
        self.setDefaultFont(QFont("Consolas", 13))

        for style, (_, text_color, paper_color, is_bold, is_italic, fill_line) in STYLES_LIST.items():
            self.setColor(QColor(text_color), style)
            self.setPaper(QColor(paper_color), style)
            self.setFont(
                QFont(
                    "Consolas",
                    13,
                    (QFont.Weight.Bold if is_bold else QFont.Weight.Normal),
                    is_italic,
                ),
                style,
            )
            self.setEolFill(fill_line, style)

    def language(self):
        return "PTYX MCQ"

    def description(self, style: int) -> str:
        if style < len(Style):
            return Style(style).name
        return ""

    def styleText(self, start: int, end: int):
        editor: EditorWidget = self.parent()
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
        # Test in https://regex101.com/
        p = re.compile(
            "|".join(
                [
                    r"^\.{4,}$",  # start of a python code section: ...........
                    r"#\w+",  # pTyX tag or variable: #TAG_NAME
                    "#[-+*=?]",  # special pTyX tags: #+, #-, #*, #=, #?
                    r"#\{",  # starts a pTyX expression: #{
                    "^[-+!] ",  # an answer (incorrect, correct or disabled)
                    r"\\\\",  # \\ (to parse python strings, it's easier to consider it as a single token)
                    r"\\'",  # \' (to parse python strings, it's easier to consider it as a single token)
                    r'\\"',  # \" (to parse python strings, it's easier to consider it as a single token)
                    r"^OR[ \t]*\n",  # OR (introduce another version of an exercise)
                    r"\\[a-zA-Z]+",  # LaTeX macro: \macro
                    "'{3}",  # '''
                    '"{3}',  # """
                    r"\n",  # \n
                    r"[ \t]+",  # space or tab (don't include newlines!)
                    r"\w+",  # potential variable names or number
                    r"\.\d+",  # number (float)
                    r"\d+\.?",  # number (float)
                    r"\W",  # non-alphanumeric symbol
                ]
            ),
            flags=re.MULTILINE,
        )

        # 'token_list' is a list of tuples: (token_name, token_len)
        token_list: list[str] = p.findall(text)

        # 4. Style the text
        # ------------------
        # 4.1 Get previous style and mode if any.
        if start > 0:
            style = Style(editor.SendScintilla(editor.SCI_GETSTYLEINDEXAT, start - 1))
            mode = STYLES_LIST[style].mode
        else:
            style = Style.DEFAULT
            mode = Mode.DEFAULT
        # 4.2 Style the text in a loop
        for i, token in enumerate(token_list):
            assert isinstance(token, str), token
            style, mode = self.get_style_and_mode(token, mode, style)
            # In setStyling, the length is the number of bytes, not the number of unicode characters !
            self.setStyling(len(bytearray(token, "utf-8")), style)
            # print(repr(token), length)

    @staticmethod
    def get_style_and_mode(token: str, mode: Mode, style: Style) -> tuple[Style, Mode]:
        if mode == Mode.PYTHON_STRING:
            if token == "\n" and style in (
                Style.PYTHON_SINGLE_QUOTE_STRING,
                Style.PYTHON_DOUBLE_QUOTE_STRING,
            ):
                style = Style.PYTHON_UNCLOSED_STRING
                mode = Mode.PYTHON
            elif token == QUOTES[style]:
                mode = Mode.PYTHON
                # No need to change style.
        elif token.startswith("...."):
            style = Style.PYTHON_BLOCK_DELIMITER
            assert token.rstrip("\n").rstrip(".") == "", token
            mode = Mode.PYTHON if mode == Mode.DEFAULT else Mode.DEFAULT
        elif token == "#PYTHON":
            style = Style.PYTHON_BLOCK_DELIMITER
            mode = Mode.PYTHON
        elif token == "#END_PYTHON" or (token == "#END" and mode == Mode.PYTHON):
            style = Style.PYTHON_BLOCK_DELIMITER
            mode = Mode.DEFAULT
        elif token == "}" and mode == Mode.EXPRESSION:
            mode = Mode.DEFAULT
            style = Style.PTYX_TAG
        elif mode in (Mode.PYTHON, mode.EXPRESSION):
            if token in REVERSED_QUOTES:
                style = REVERSED_QUOTES[token]
                mode = Mode.PYTHON_STRING
            elif iskeyword(token) or token in ("let", "case", "match"):
                style = Style.PYTHON_KEYWORD
            elif token in ALL_BUILTINS:
                style = Style.PYTHON_BUILTIN
            elif token.strip(".").isdigit():
                style = Style.PYTHON_INT
            else:
                style = Style.PYTHON_BLOCK
        else:
            # print(repr(token))
            if token.startswith("#"):
                if token[1:] in TAGS:
                    style = Style.PTYX_TAG
                elif token == "#{":
                    mode = Mode.EXPRESSION
                    style = Style.PTYX_TAG
                elif token[1:].isalpha():
                    style = Style.PTYX_VARIABLE
                else:
                    style = Style.DEFAULT
            elif token.startswith("\\") and token[1:].isalpha():
                style = Style.PTYX_LATEX_MACRO
            elif token == "- ":
                style = Style.MCQ_INCORRECT_ANSWER
            elif token == "+ ":
                style = Style.MCQ_CORRECT_ANSWER
            elif token == "! ":
                style = Style.MCQ_NEUTRALIZED_ANSWER
            elif token.startswith("OR") and token.endswith("\n"):
                style = Style.MCQ_OR
            else:
                # Default style
                style = Style.DEFAULT
        return style, mode
