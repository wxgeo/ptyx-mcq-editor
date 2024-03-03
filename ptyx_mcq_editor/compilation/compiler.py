import contextlib
from base64 import urlsafe_b64encode
from pathlib import Path
from typing import Literal, TypedDict, NotRequired

from PyQt6.QtCore import QObject, pyqtSignal

from ptyx.compilation import compile_latex_to_pdf, SingleFileCompilationInfo
from ptyx.errors import PythonBlockError, PtyxDocumentCompilationError
from ptyx.extensions.extended_python import main
from ptyx.latex_generator import Compiler

from ptyx_mcq.make.exercises_parsing import wrap_exercise


class CompilerWorkerInfo(TypedDict):
    code: str
    compilation_info: NotRequired[SingleFileCompilationInfo]
    error: NotRequired[PtyxDocumentCompilationError]
    info: NotRequired[str]


def path_hash(path: Path | str) -> str:
    return urlsafe_b64encode(hash(str(path)).to_bytes(8, signed=True)).decode("ascii").rstrip("=")


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


class CompilerWorker(QObject):
    def __init__(self, code: str, doc_path: Path, tmp_dir: Path, pdf=False):
        super().__init__(None)
        self.code = code
        self.doc_path = doc_path
        assert self.doc_path is not None
        self.pdf = pdf
        self.tmp_dir = tmp_dir

    finished = pyqtSignal(dict, name="finished")
    # progress = pyqtSignal(int)

    def get_temp_path(self, suffix: Literal["tex", "pdf"]) -> Path:
        """Get the path of a temporary file corresponding to the current document."""
        return self.tmp_dir / f"{self.doc_path.stem}-{path_hash(self.doc_path)}.{suffix}"

    def compile_latex(self):
        latex_file = self.get_temp_path("tex")
        compilation_info = compile_latex_to_pdf(latex_file, dest=self.main_window.tmp_dir)
        self.finished.emit(compilation_info)

    def _is_single_exercise(self) -> bool:
        return self.doc_path.suffix == ".ex"

    def generate(self) -> None:
        """Generate a LaTeX file.

        If `doc_path` is None, the LaTeX file corresponds to the current edited document.
        Else, `doc_path` must point to a .ptyx or .ex file.
        """
        print("coucou")
        # main_window = self.main_window
        # doc = main_window.settings.current_doc
        # editor = main_window.current_mcq_editor
        # latex_path = self._latex_file_path(doc_path=doc_path)
        # if doc is None or editor is None or latex_path is None:
        #     return
        # code = editor.text() if doc_path is None else doc_path.read_text(encoding="utf8")
        code = inject_labels(self.code)
        return_data: CompilerWorkerInfo = {"code": code}
        compiler = Compiler()
        options = {"MCQ_KEEP_ALL_VERSIONS": True, "PTYX_WITH_ANSWERS": True}
        if self._is_single_exercise():
            print("\n == Exercise detected. == \n")
            code = wrap_exercise(code, self.doc_path)
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
            with contextlib.chdir(self.doc_path.parent):
                latex = compiler.parse(code=code, **options)  # type: ignore
        except BaseException as e:
            print(e)
            latex = ""
            if isinstance(e, PythonBlockError):
                # editor.display_error(code=code, error=e)
                return_data["error"] = e

        latex_file = self.get_temp_path("tex")
        latex_file.write_text(latex, encoding="utf8")
        if self.pdf:
            return_data["compilation_info"] = compile_latex_to_pdf(latex_file, dest=self.tmp_dir)
        self.finished.emit(return_data)
