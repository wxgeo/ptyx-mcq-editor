import contextlib
import pickle
from base64 import urlsafe_b64encode
from multiprocessing import Process, Queue
from multiprocessing.queues import Queue as QueueType
from pathlib import Path
from traceback import print_exception
from typing import Literal, TypedDict, NotRequired, Any

from PyQt6.QtCore import QObject, pyqtSignal

from ptyx.compilation import compile_latex_to_pdf, SingleFileCompilationInfo
from ptyx.errors import PtyxDocumentCompilationError
from ptyx.extensions.extended_python import main
from ptyx.latex_generator import Compiler
from ptyx.shell import red, yellow

from ptyx_mcq.make.exercises_parsing import wrap_exercise
from ptyx_mcq.tools.misc import CaptureLog


class PreviewCompilerWorkerInfo(TypedDict):
    code: str
    doc_path: Path
    compilation_info: NotRequired[SingleFileCompilationInfo]
    error: NotRequired[BaseException]
    info: NotRequired[str]
    log: str


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


def compile_code(queue: QueueType, code: str, options: dict[str, Any]) -> None:
    """Compile code from another process, using queue to give back information."""
    try:
        compiler = Compiler()
        latex = compiler.parse(code=code, **options)
        queue.put(latex)
    except BaseException as e:
        pickle_incompatibility = False
        try:
            if type(pickle.loads(pickle.dumps(e))) is not type(e):
                pickle_incompatibility = True
        except BaseException:
            pickle_incompatibility = True
            raise
        finally:
            if pickle_incompatibility:
                print(red(f"ERROR: Exception {type(e)} is not compatible with pickle!"))
                print(yellow("Please open a bug report about it!"))
                # Do not try to serialize this incompatible exception,
                # this will fail, and may even generate segfaults!
                # Let's use a vanilla `RuntimeError` instead.
                # (Yet, we should make this exception compatible with pickle asap...)
                queue.put(RuntimeError(str(e)))
            else:
                queue.put(e)
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        print(e, type(e), repr(e))
        print_exception(e)
        print("xxxxxxxxxxxxxxxxxxxxxxxxxxxx")


class PreviewCompilerWorker(QObject):
    def __init__(self, code: str, doc_path: Path, doc_id: int, tmp_dir: Path, pdf=False):
        super().__init__(None)
        self.log_already_captured = False
        self.code = code
        self.doc_path = doc_path
        self.doc_id = doc_id
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
        return_data: PreviewCompilerWorkerInfo = {"code": self.code, "doc_path": self.doc_path, "log": ""}
        # log: CaptureLog | str = "Error, log couldn't be captured!"
        with CaptureLog() as log:
            try:
                return_data = self._generate()
            finally:
                return_data["log"] = log.getvalue()
                print("End of task: emit 'finished' event.")
                self.finished.emit(return_data)

    def _generate(self) -> PreviewCompilerWorkerInfo:
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
        return_data: PreviewCompilerWorkerInfo = {"code": code, "doc_path": self.doc_path, "log": "No log."}
        options = {"MCQ_KEEP_ALL_VERSIONS": True, "PTYX_WITH_ANSWERS": True, "PTYX_NUM": self.doc_id}
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
            # Do *NOT* join process while there is still data in the queue.
            # See multiprocessing documentation concerning potential resulting deadlocks, and also:
            # https://stackoverflow.com/questions/31665328/python-3-multiprocessing-queue-deadlock-when-calling-join-before-the-queue-is-em
            # process.join()  <- So, don't do this!
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
