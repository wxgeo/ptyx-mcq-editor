import re
from pathlib import Path
from typing import TYPE_CHECKING

import ptyx_mcq
from PyQt6 import Qsci
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QColor
from ptyx.latex_generator import Compiler

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

if TYPE_CHECKING:
    pass


class LatexViewer(Qsci.QsciScintilla, EnhancedWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.setMarginWidth(0, "0000")
        self.setMarginsForegroundColor(QColor("#ff888888"))
        self.setLexer(Qsci.QsciLexerTeX(self))

    def _latex_file_path(self, doc_path: Path = None) -> Path | None:
        """Get the path of the current latex file."""
        return self.main_window.get_temp_path("tex", doc_path=doc_path)

    def _is_single_exercise(self, doc_path: Path = None) -> bool:
        try:
            if doc_path is None:
                doc_path = self.main_window.settings.current_doc.path
            return doc_path.suffix == ".ex"
        except AttributeError:
            return False

    def generate_latex(self, doc_path: Path = None) -> None:
        """Generate a LaTeX file.

        If `doc_path` is None, the LaTeX file corresponds to the current edited document.
        Else, `doc_path` must point to a .ptyx or .ex file.
        """
        main_window = self.main_window
        doc = main_window.settings.current_doc
        editor = main_window.current_mcq_editor
        latex_path = self._latex_file_path(doc_path=doc_path)
        if doc is None or editor is None or latex_path is None:
            return
        code = editor.text() if doc_path is None else doc_path.read_text(encoding="utf8")
        compiler = Compiler()
        options = {"MCQ_KEEP_ALL_VERSIONS": True, "PTYX_WITH_ANSWERS": True}
        if self._is_single_exercise(doc_path):
            print("\n == Exercise detected. == \n")
            code = self._wrap_ptyx_code(code)
            options["MCQ_REMOVE_HEADER"] = True
            options["MCQ_PREVIEW_MODE"] = True
            print(code)
        else:
            options["MCQ_DISPLAY_QUESTION_TITLE"] = True
        try:
            latex = compiler.parse(code=code, **options)  # type: ignore
        except BaseException as e:
            print(e)
            latex = ""
        self.setText(latex)
        latex_path.write_text(latex, encoding="utf8")

    @staticmethod
    def _wrap_ptyx_code(code: str) -> str:
        """For mcq exercises, automatically add a minimal header to make it compilation-ready."""
        template = (Path(ptyx_mcq.__file__).parent / "templates/original/new.ptyx").read_text()
        if not code.lstrip().startswith("* "):
            code = "* \n" + code
        # re.sub() doesn't seem to work when "\dfrac" is in the replacement string... using re.split() instead.
        before, _, after = re.split("(<<<.+>>>)", template, flags=re.MULTILINE | re.DOTALL)
        return f"{before}\n<<<\n{code}\n>>>\n{after}"

    def _get_latex(self, doc_path: Path = None) -> str:
        latex_path = self._latex_file_path(doc_path=doc_path)
        if latex_path is None or not latex_path.is_file():
            return ""
        return latex_path.read_text(encoding="utf8")

    # def _get_latex(self) -> str:
    #     if self.main_window.current_mcq_editor is None:
    #         return ""
    #     content = self.main_window.current_mcq_editor.text()
    #     template = (Path(ptyx_mcq.__file__).parent / "templates/original/new.ptyx").read_text()
    #     if not content.lstrip().startswith("* "):
    #         content = "* \n" + content
    #     # re.sub() doesn't seem to work when "\dfrac" is in the replacement string... using re.split() instead.
    #     before, _, after = re.split("(<<<.+>>>)", template, flags=re.MULTILINE | re.DOTALL)
    #     ptyx_code = f"{before}\n<<<\n{content}\n>>>\n{after}"
    #     compiler = Compiler()
    #     latex = compiler.parse(
    #         code=ptyx_code, MCQ_KEEP_ALL_VERSIONS=True, PTYX_WITH_ANSWERS=True, MCQ_REMOVE_HEADER=True
    #     )
    #     return latex

    def load(self, doc_path: Path = None) -> None:
        self.setText(self._get_latex(doc_path=doc_path))
