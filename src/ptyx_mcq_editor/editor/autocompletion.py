"""
Implement autocompletion in the editor.
"""

from typing import TYPE_CHECKING

import jedi  # type: ignore[import-untyped]
from PIL.ImageChops import offset
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.Qsci import QsciScintilla, QsciAPIs
import traceback

if TYPE_CHECKING:
    from ptyx_mcq_editor.editor.editor_widget import EditorWidget


class CompletionWorker(QThread):
    """Runs jedi in a background thread to avoid blocking the UI."""

    completions_ready = pyqtSignal(list)  # list[str]
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
            self.completions_ready.emit(names)
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

    def __init__(self, editor: "EditorWidget"):
        self.editor = editor
        self._worker: CompletionWorker | None = None
        self._apis: QsciAPIs | None = None
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
        ed.setAutoCompletionThreshold(1)  # show after 1 char
        ed.setAutoCompletionCaseSensitivity(True)
        ed.setAutoCompletionReplaceWord(False)
        ed.setAutoCompletionUseSingle(QsciScintilla.AutoCompletionUseSingle.AcusNever)

        # If you already have a lexer attached:
        lexer = ed.lexer()
        if lexer:
            self._apis = QsciAPIs(lexer)
            self._apis.prepare()

    def _on_text_changed(self):
        self._debounce.start()  # restart debounce timer

    def _on_cursor_moved(self, line: int, col: int):
        # Immediately hide completion if we moved out of a Python block
        if not self.editor.is_python_block_code(line, col):
            self.editor.cancelList()

    def _trigger_completion(self) -> None:
        ed = self.editor
        line, col = ed.getCursorPosition()

        python_code = self.editor.python_content.current_python_code(line, col)
        if python_code is None or self.editor.python_content.is_extended_python(line):
            # We are not inside a Python code block, or this line does not follow the Python syntax.
            return

        # Kill previous worker if still running
        if self._worker and self._worker.isRunning():
            self._worker.terminate()

        _virtual_position = self.editor.python_content.virtual_position(line, col)
        assert _virtual_position is not None
        jedi_line, jedi_col = _virtual_position
        # jedi line numbers are 1-based
        jedi_line += 1

        self._worker = CompletionWorker(python_code, jedi_line, jedi_col)
        self._worker.completions_ready.connect(self._on_completions_ready)
        self._worker.start()

    def _on_completions_ready(self, names: list[str]) -> None:
        if not self._apis or not names:
            return

        self._apis.clear()
        for name in names:
            self._apis.add(name)
        self._apis.prepare()

        # Trigger the popup (only if user is still typing)
        self.editor.autoCompleteFromAPIs()
