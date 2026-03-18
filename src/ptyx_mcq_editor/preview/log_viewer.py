from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6 import Qsci
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QColor

from ptyx_mcq_editor.preview.log_lexer import LogLexer
from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

if TYPE_CHECKING:
    pass


class LogViewer(Qsci.QsciScintilla, EnhancedWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setMarginsForegroundColor(QColor("#ff888888"))
        self.setLexer(LogLexer(self))
        # Qsci.QsciLexerDiff
        # self.setLexer(Qsci.QsciLexerPython(self))
        # self.SendScintilla(QsciScintilla.SCI_SETLEXER, QsciScintilla.SCLEX_PYTHON, 0)
        # Qsci.QsciScintillaBase.SCLEX_ERRORLIST)

    def _log_file_path(self, doc_path: Path = None) -> Path | None:
        """Get the path of the current latex file."""
        return self.main_window.get_temp_path("ptyx-log", doc_path=doc_path)

    def _get_log(self, doc_path: Path = None) -> str:
        log_path = self._log_file_path(doc_path=doc_path)
        if log_path is None or not log_path.is_file():
            return ""
        return log_path.read_text(encoding="utf8")

    def write_log(self, doc_path: Path = None) -> None:
        """Save pTyX log content on disk.

        If `doc_path` is None, the LaTeX file corresponds to the current edited document.
        Else, `doc_path` must point to a .ptyx or .ex file.
        """
        log_path = self._log_file_path(doc_path=doc_path)
        if log_path is not None:
            log_path.write_text(self.text(), encoding="utf8")

    def load(self, doc_path: Path = None) -> None:
        self.setText(self._get_log(doc_path=doc_path))
