import contextlib
import io
import sys
from base64 import urlsafe_b64encode
from multiprocessing import Process, Queue
from multiprocessing.queues import Queue as QueueType
from pathlib import Path
from traceback import print_exception
from types import TracebackType
from typing import Literal, TypedDict, NotRequired, Type, Any

from PyQt6.QtCore import QObject, pyqtSignal

from ptyx.compilation import compile_latex_to_pdf, SingleFileCompilationInfo
from ptyx.errors import PtyxDocumentCompilationError
from ptyx.extensions.extended_python import main
from ptyx.latex_generator import Compiler

from ptyx_mcq.make.exercises_parsing import wrap_exercise


class CompilerWorkerInfo(TypedDict):
    code: str
    compilation_info: NotRequired[SingleFileCompilationInfo]
    error: NotRequired[BaseException]
    info: NotRequired[str]
    log: NotRequired[str]


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


class CaptureLog(io.StringIO):
    """Class used to capture a copy of stdout and stderr output."""

    def __enter__(self) -> "CaptureLog":
        self.previous_stdout = sys.stdout
        self.previous_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        sys.stdout = self.previous_stdout
        sys.stderr = self.previous_stderr
        self.close()

    def write(self, s: str, /) -> int:
        self.previous_stdout.write(s)
        return super().write(s)


# def capture_log(f: Callable) -> Callable:
#     """Decorator used to capture a copy of stdout and stderr and print their content in log tab."""
#
#     @wraps(f)
#     def wrapper(self: "CompilerWorker", *args, **kw):
#         if not self.log_already_captured:
#             try:
#                 with CaptureLog() as log:
#                     self.log_already_captured = True
#                     f(self, *args, **kw)
#                     self.log_viewer.setText(log.getvalue())
#                     self.log_viewer.write_log()
#             finally:
#                 self.log_already_captured = False
#
#     return wrapper


def compile_code(queue: QueueType, code: str, options: dict[str, Any]) -> None:
    """Compile code from another process, using queue to give back information."""
    try:
        compiler = Compiler()
        latex = compiler.parse(code=code, **options)
        queue.put(latex)
    except BaseException as e:
        queue.put(e)
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        print(e, type(e), repr(e))
        print_exception(e)
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxx")


class CompilerWorker(QObject):
    def __init__(self, code: str, doc_path: Path, tmp_dir: Path, pdf=False):
        super().__init__(None)
        self.log_already_captured = False
        self.code = code
        self.doc_path = doc_path
        assert self.doc_path is not None
        self.pdf = pdf
        self.tmp_dir = tmp_dir

    finished = pyqtSignal(dict, name="finished")
    process_started = pyqtSignal(Process, QueueType, name="process_started")
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
        return_data: CompilerWorkerInfo = {"code": self.code}
        log: CaptureLog | str = "Error, log couldn't be captured!"
        try:
            with CaptureLog() as log:
                return_data = self._generate()
        finally:
            return_data["log"] = str(log)
            print("End of task: emit 'finished' event.")
            self.finished.emit(return_data)

    def _generate(self) -> CompilerWorkerInfo:
        """Generate a LaTeX file.

        If `doc_path` is None, the LaTeX file corresponds to the current edited document.
        Else, `doc_path` must point to a .ptyx or .ex file.
        """
        # main_window = self.main_window
        # doc = main_window.settings.current_doc
        # editor = main_window.current_mcq_editor
        # latex_path = self._latex_file_path(doc_path=doc_path)
        # if doc is None or editor is None or latex_path is None:
        #     return
        # code = editor.text() if doc_path is None else doc_path.read_text(encoding="utf8")
        code = inject_labels(self.code)
        return_data: CompilerWorkerInfo = {"code": code}
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
        # Change current directory to the parent directory of the ptyx file.
        # This allows for relative paths in include directives when compiling.
        with contextlib.chdir(self.doc_path.parent):
            queue: Queue = Queue()
            process = Process(target=compile_code, args=(queue, code, options))
            # Share process with main thread, to enable user to kill it if needed.
            # This may prove useful if there is an infinite loop in user code
            # for example.
            self.process_started.emit(process, queue)
            process.start()
            print(f"Waiting for process {process.pid}")
            # process.join()
            print(f"End of process {process.pid}")
        match queue.get():
            case str(latex):
                pass
            case BaseException() as e:
                latex = ""
                return_data["error"] = e
            case None:
                print("Queue value is `None`: the process was most probably aborted...")
                latex = ""
                return_data["error"] = PtyxDocumentCompilationError("compilation interrupted.")
            case other:
                raise ValueError(f"Unrecognized data: {other}")
        print("Process data successfully recovered.")

        latex_file = self.get_temp_path("tex")
        latex_file.write_text(latex, encoding="utf8")
        if self.pdf:
            return_data["compilation_info"] = compile_latex_to_pdf(latex_file, dest=self.tmp_dir)
        return return_data
