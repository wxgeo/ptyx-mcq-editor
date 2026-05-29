"""
Implement autocompletion in the editor.
"""

from typing import TYPE_CHECKING

import jedi  # type: ignore[import-untyped]
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.Qsci import QsciScintilla, QsciAPIs
import traceback


from ptyx.pretty_print import print_warning

if TYPE_CHECKING:
    from ptyx_mcq_editor.editor.editor_widget import EditorWidget


class CompletionWorker(QThread):
    """Runs jedi in a background thread to avoid blocking the UI."""

    completion_ready = pyqtSignal(list)  # list[str]
    completion_error = pyqtSignal(str)  # carries the traceback

    def __init__(self, source: str, line: int, column: int, path: str = ""):
        super().__init__()
        self.source = source
        self.line = line
        self.column = column
        self.path = path

    def run(self):
        # noinspection PyBroadException
        try:
            script = jedi.Script(self.source, path=self.path)
            completions = script.complete(self.line, self.column)
            names = [c.name for c in completions]
            self.completion_ready.emit(names)
        except Exception:
            self.completion_error.emit(traceback.format_exc())


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
        self._worker: CompletionWorker | None = None
        self._apis: QsciAPIs | None = None
        # Last char and last word before the cursor.
        self._last_char = ""
        self._current_word = ""
        # Use a timer to avoid calling autocompletion when the user is still writing.
        # Every time the user modifies the text, the timer will be reset.
        self._debounce = QTimer()
        self._debounce.setSingleShot(True)
        self._debounce.setInterval(300)  # ms after typing stops
        self._debounce.timeout.connect(self._trigger_completion)

        self._setup_scintilla()
        editor.textChanged.connect(self._on_text_changed)
        editor.cursorPositionChanged.connect(self._on_cursor_moved)

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

    def _on_cursor_moved(self, line: int, col: int):
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

        self._worker = CompletionWorker(python_code, jedi_line, jedi_col)
        self._worker.completion_ready.connect(self._on_completion_ready)
        self._worker.completion_error.connect(self._on_completion_error)
        self._worker.start()

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

    def _on_completion_error(self, message: str) -> None:
        print(message)
        print_warning("Autocompletion failed.")
