import contextlib
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6 import Qsci
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QColor
from ptyx.extensions.extended_python import main
from ptyx.latex_generator import Compiler
from ptyx.errors import PythonBlockError
from ptyx_mcq.make.exercises_parsing import wrap_exercise

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

if TYPE_CHECKING:
    pass


def inject_labels(code: str) -> str:
    """Inject a unique label in each python code snippet.

    This make identification and highlighting easier when some python code fails."""
    # It is much easier to parse extended python code first,
    # so as to convert `....\n[xxx]\n....` blocks into `#PYTHON\n[xxx]\n#END_PYTHON` blocks.
    # So, we will call `main(code)` first.
    return "\n".join(
        line + f":{i}:" if line.rstrip().endswith("#PYTHON") else line
        for i, line in enumerate(main(code).split("\n"), start=1)
    )


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
        if doc_path is None:
            doc_path = self.main_window.settings.current_doc_path
        return doc_path is not None and doc_path.suffix == ".ex"

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
        code = inject_labels(code)
        compiler = Compiler()
        options = {"MCQ_KEEP_ALL_VERSIONS": True, "PTYX_WITH_ANSWERS": True}
        if self._is_single_exercise(doc_path):
            print("\n == Exercise detected. == \n")
            code = wrap_exercise(code, doc_path)
            options["MCQ_REMOVE_HEADER"] = True
            options["MCQ_PREVIEW_MODE"] = True
            print("Temporary pTyX file code:")
            print("\n" + 5 * "---✂---")
            print(code)
            print(5 * "---✂---" + "\n")
        else:
            options["MCQ_DISPLAY_QUESTION_TITLE"] = True
        try:
            # Change current directory to the parent directory of the ptyx file.
            # This allows for relative paths in include directives when compiling.
            with contextlib.chdir(
                main_window.settings.current_directory if doc_path is None else doc_path.parent
            ):
                latex = compiler.parse(code=code, **options)  # type: ignore
        except BaseException as e:
            print(e)
            latex = ""
            if isinstance(e, PythonBlockError):
                editor.display_error(code=code, error=e)
        self.setText(latex)
        latex_path.write_text(latex, encoding="utf8")

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
