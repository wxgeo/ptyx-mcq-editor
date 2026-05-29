"""
Implement autocompletion in the editor.
"""

import textwrap
from typing import TYPE_CHECKING

import jedi  # type: ignore[import-untyped]
from jedi.api.classes import Name  # type: ignore[import-untyped]
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, QPoint
from PyQt6.Qsci import QsciScintilla, QsciAPIs
import traceback

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import PythonLexer

from ptyx.pretty_print import print_warning

if TYPE_CHECKING:
    from ptyx_mcq_editor.editor.editor_widget import EditorWidget

from PyQt6.QtWidgets import QWidget, QTextEdit, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent, QTextOption

from ptyx.context import GLOBAL_CONTEXT


def _format_docstring(signature: str | None, docstring: str) -> str:
    formatter = HtmlFormatter(nowrap=True, style="default")
    css = formatter.get_style_defs()

    sig_html = ""
    if signature:
        sig_html = highlight("def " + signature, PythonLexer(), HtmlFormatter(nowrap=True, style="default"))
        sig_html = f'<code>{sig_html}</code><hr style="border:none;border-top:1px solid #ccc;margin:4px 0;">'

    body = docstring.strip().replace("\n", "<br>")

    return f"""
    <style>{css}</style>
    <div>{sig_html}</div>
    <div>{body}</div>
    """


class DocstringPopup(QWidget):
    """A persistent tooltip-like popup for displaying docstrings.
    Closes on Escape or click outside.
    """

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setFrameStyle(0)
        self._text.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        layout.addWidget(self._text)

        # Match QToolTip appearance
        self.setStyleSheet("""
            QWidget { background: #ffffdc; border: 1px solid #aaaaaa; }
            QTextEdit { background: #ffffdc; }
        """)

    def show_at(self, global_pos: QPoint, signature: str | None, docstring: str) -> None:
        self._text.setHtml(_format_docstring(signature, docstring))
        # Size to content
        doc = self._text.document()
        assert doc is not None
        doc.setTextWidth(500)
        self.resize(int(doc.size().width()) + 16, int(doc.size().height()) + 16)
        self.move(global_pos)
        self.show()

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if event and event.key() == Qt.Key.Key_Escape:
            self.hide()
        else:
            super().keyPressEvent(event)

    # def mousePressEvent(self, event) -> None:
    #     self.hide()


class Worker(QThread):
    """
    Runs jedi in a background thread to avoid blocking the UI.

    Abstract class.
    """

    ready = pyqtSignal(list)  # list[str]
    error = pyqtSignal(str)  # carries the traceback

    def __init__(self, source: str, line: int, column: int):
        super().__init__()
        self.source = source
        self.line = line
        self.column = column

    def run(self):
        raise NotImplementedError


class CompletionWorker(Worker):
    """Runs jedi in a background thread to avoid blocking the UI."""

    def run(self):
        # noinspection PyBroadException
        try:
            script = jedi.Interpreter(self.source, [GLOBAL_CONTEXT])
            completions = script.complete(self.line, self.column)
            names = [c.name for c in completions]
            if names:
                self.ready.emit(names)
        except Exception:
            self.error.emit(traceback.format_exc())


class SignatureWorker(Worker):
    """Runs jedi in a background thread to avoid blocking the UI."""

    def run(self):
        # noinspection PyBroadException
        try:
            script = jedi.Interpreter(self.source, [GLOBAL_CONTEXT])
            signatures = script.get_signatures(self.line, self.column)
            if not signatures:
                return
            self.ready.emit([signatures[0].to_string()])
        except Exception:
            self.error.emit(traceback.format_exc())


class PythonAutoCompleter:
    """
    Attach to a QsciScintilla editor.
    Provides dynamic, jedi-powered Python completion inside Python blocks
    of a LaTeX template.

    Usage:
        self.completer = PythonAutoCompleter(self.editor)
    """

    def __init__(self, editor: "EditorWidget", minimal_char_count=1):
        self.editor = editor
        self.minimal_char_count = minimal_char_count
        self._worker: Worker | None = None
        self._apis: QsciAPIs | None = None
        # Last char and last word before the cursor.
        self._last_char = ""
        self._current_word = ""
        self._current_pos = 0
        # Use a timer to avoid calling autocompletion when the user is still writing.
        # Every time the user modifies the text, the timer will be reset.
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)  # ms after typing stops
        self._debounce.timeout.connect(self._trigger_completion)

        self._setup_scintilla()
        editor.textChanged.connect(self._on_text_changed)
        editor.cursorPositionChanged.connect(self._on_cursor_moved)
        self.docstring_popup = DocstringPopup(editor)

    def _setup_scintilla(self) -> None:
        ed = self.editor

        # Use Python lexer for syntax highlighting (you may already have this)
        # If your editor uses a custom lexer, skip or adapt this block.

        # Autocompletion settings
        ed.setAutoCompletionSource(QsciScintilla.AutoCompletionSource.AcsAPIs)
        ed.setAutoCompletionThreshold(self.minimal_char_count)  # show after 1 char
        ed.setAutoCompletionCaseSensitivity(True)
        ed.setAutoCompletionReplaceWord(False)
        ed.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)

        # If you already have a lexer attached:
        lexer = ed.lexer()
        if lexer:
            self._apis = QsciAPIs(lexer)
            self._apis.prepare()

    def _on_text_changed(self):
        self._debounce.start()
        self.docstring_popup.hide()

    def _on_cursor_moved(self, line: int, col: int):
        self.docstring_popup.hide()
        # Immediately hide completion if we moved out of a Python block
        if not self.editor.is_python_block_code(line, col):
            self.editor.cancelList()

    def _trigger_completion(self) -> None:
        ed = self.editor
        line, col = ed.getCursorPosition()

        python_code = self.editor.python_content.current_python_code(line, col)
        # jedi line numbers are 1-based
        virtual_position = self.editor.python_content.virtual_position(line, col, first_line=1)
        if python_code is None or virtual_position is None:
            # We are not inside a Python code block.
            return
        if self.editor.python_content.is_extended_python(line):
            # The current line does not follow the Python syntax (it is "extended python", see pTyX plugin).
            return

        # Kill previous worker if still running
        if self._worker and self._worker.isRunning():
            self._worker.terminate()

        jedi_line, jedi_col = virtual_position
        print(f"{jedi_line=}, {jedi_col=}")

        current_line = python_code.split("\n")[jedi_line - 1]
        self._last_char = current_line[jedi_col - 1 : jedi_col]
        # print(f"{self._last_char=}")

        pos = ed.positionFromLineIndex(line, col)
        word_start = self.editor.SendScintilla(QsciScintilla.SCI_WORDSTARTPOSITION, pos, True)
        word_end = self.editor.SendScintilla(QsciScintilla.SCI_WORDENDPOSITION, pos, True)
        self._current_word = self.editor.text()[word_start:word_end]
        self._current_pos = ed.positionFromLineIndex(line, col)

        # Either ask for autocompletion, or for the signature of the function/method, depending on the last char.
        display_signature = self._last_char in ("(", ",")
        worker_class = SignatureWorker if display_signature else CompletionWorker
        self._worker = worker_class(python_code, jedi_line, jedi_col)
        self._worker.ready.connect(
            self._on_signature_ready if display_signature else self._on_completion_ready
        )
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_signature_ready(self, hint: list[str]) -> None:
        wrapped = textwrap.fill(hint[0], width=72)
        self.editor.SendScintilla(QsciScintilla.SCI_CALLTIPSHOW, self._current_pos, wrapped.encode("utf-8"))

    def _on_completion_ready(self, names: list[str]) -> None:
        if not self._apis or not names:
            return
        if len(names) == 1 and names[0] == self._current_word:
            # No need to show the suggestion, since it matches the current text!
            self.editor.cancelList()
            return
        if self._last_char == ".":
            # Force autocompletion popup to appear, bypassing QScintilla internal logic.
            # This is used to trigger autocompletion suggestions after a dot.
            # Bypass QsciAPIs entirely — show the raw list directly
            # SCI_AUTOCSHOW(int lenEntered, const char *itemList)
            # lenEntered = characters of the stem already typed (0 after a dot)
            item_list = " ".join(
                sorted(name for name in names if name[0] != "_")
            )  # space-separated, must be sorted
            self.editor.SendScintilla(QsciScintilla.SCI_AUTOCSETSEPARATOR, ord(" "))
            self.editor.SendScintilla(
                QsciScintilla.SCI_AUTOCSHOW,
                0,  # lenEntered
                item_list.encode("utf-8"),
            )
        else:
            self._apis.clear()
            for name in names:
                self._apis.add(name)
            self._apis.prepare()

            # Trigger the popup (only if user is still typing)
            self.editor.autoCompleteFromAPIs()

    def _on_error(self, message: str) -> None:
        print(message)
        print_warning("Autocompletion or signature failed.")

    def trigger_f1_docstring(self) -> None:
        line, col = self.editor.getCursorPosition()
        python_code = self.editor.python_content.current_python_code(line, col)
        virtual_position = self.editor.python_content.virtual_position(line, col, first_line=1)
        if python_code is None or virtual_position is None:
            return
        jedi_line, jedi_col = virtual_position
        script = jedi.Interpreter(python_code, [GLOBAL_CONTEXT])
        found: list[Name] = script.infer(jedi_line, jedi_col)
        if not found:
            return
        func = found[0]

        pos = self.editor.positionFromLineIndex(line, col)
        x = self.editor.SendScintilla(QsciScintilla.SCI_POINTXFROMPOSITION, 0, pos)
        y = self.editor.SendScintilla(QsciScintilla.SCI_POINTYFROMPOSITION, 0, pos)
        global_pos = self.editor.mapToGlobal(QPoint(x, y + 20))
        try:
            signature = func.get_signatures()[0].to_string()
        except IndexError:
            signature = ""
        doc = func.docstring(raw=True)

        self.docstring_popup.show_at(global_pos, signature, doc)
