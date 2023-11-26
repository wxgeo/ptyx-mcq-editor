import re
from pathlib import Path
from typing import TYPE_CHECKING

import ptyx_mcq
from PyQt6 import Qsci
from ptyx.latex_generator import Compiler

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

if TYPE_CHECKING:
    pass


class LatexViewer(Qsci.QsciScintilla, EnhancedWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.setLexer(Qsci.QsciLexerTeX(self))

    def _get_latex(self) -> str:
        template = (Path(ptyx_mcq.__file__).parent / "templates/original/new.ptyx").read_text()
        content = self.get_main_window().current_mcq_editor.text()
        if not content.lstrip().startswith("* "):
            content = "* \n" + content
        # re.sub() doesn't seem to work when "\dfrac" is in the replacement string... using re.split() instead.
        before, _, after = re.split("(<<<.+>>>)", template, flags=re.MULTILINE | re.DOTALL)
        ptyx_code = f"{before}\n<<<\n{content}\n>>>\n{after}"
        compiler = Compiler()
        latex = compiler.parse(
            code=ptyx_code, MCQ_KEEP_ALL_VERSIONS=True, PTYX_WITH_ANSWERS=True, MCQ_REMOVE_HEADER=True
        )
        return latex

    def load(self) -> str:
        latex = self._get_latex()
        self.setText(latex)
        return latex
