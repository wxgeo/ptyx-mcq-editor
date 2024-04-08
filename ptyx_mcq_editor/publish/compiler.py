import contextlib
import io
import multiprocessing
import os
import pickle
import sys
from dataclasses import dataclass
from multiprocessing import Process, Queue
from multiprocessing.queues import Queue as QueueType
from pathlib import Path
from traceback import print_exception
from types import TracebackType
from typing import TypedDict, NotRequired, Type

from PyQt6.QtCore import QObject, pyqtSignal

from ptyx.compilation import make_files, MultipleFilesCompilationInfo
from ptyx.errors import PtyxDocumentCompilationError
from ptyx.shell import red, yellow, print_info
from ptyx_mcq.make.make import DEFAULT_PTYX_MCQ_COMPILATION_OPTIONS, generate_config_file


@dataclass
class ProcessInfo:
    process: Process
    queue: QueueType


class CompilerWorkerInfo(TypedDict):
    doc_path: Path
    compilation_info: NotRequired[MultipleFilesCompilationInfo]
    error: NotRequired[BaseException]
    info: NotRequired[str]
    log: str


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


def compile_file(ptyx_filename: Path, number_of_documents: int, queue: QueueType) -> None:
    """Compile code from another process, using queue to give back information."""
    try:
        compilation_info, compiler = make_files(
            ptyx_filename,
            number_of_documents=number_of_documents,
            options=DEFAULT_PTYX_MCQ_COMPILATION_OPTIONS,
        )
        # Don't forget to generate config file!
        generate_config_file(compiler)
        config_file = ptyx_filename.with_suffix(".ptyx.mcq.config.json")
        assert config_file.is_file()
        print_info(f"Configuration file generated: '{config_file}'.")
        queue.put(compilation_info)
    except BaseException as e:
        pickle_incompatibility = False
        try:
            if type(pickle.loads(pickle.dumps(e))) != type(e):
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


class CompilerWorker(QObject):
    def __init__(self, doc_path: Path, number_of_documents: int):
        super().__init__(None)
        self.doc_path = doc_path
        self.number_of_documents = number_of_documents
        assert self.doc_path is not None

    finished = pyqtSignal(dict, name="finished")
    process_started = pyqtSignal(ProcessInfo, name="process_started")
    # progress = pyqtSignal(int)

    # def compile_latex(self):
    #     latex_file = self.get_temp_path("tex")
    #     compilation_info = compile_latex_to_pdf(latex_file, dest=self.main_window.tmp_dir)
    #     self.finished.emit(compilation_info)

    def generate(self) -> None:
        return_data: CompilerWorkerInfo = {"doc_path": self.doc_path, "log": ""}
        # log: CaptureLog | str = "Error, log couldn't be captured!"
        with CaptureLog() as log:
            try:
                return_data = self._generate()
            finally:
                return_data["log"] = log.getvalue()
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
        return_data: CompilerWorkerInfo = {"doc_path": self.doc_path, "log": "No log."}
        # Change current directory to the parent directory of the ptyx file.
        # This allows for relative paths in include directives when compiling.
        with contextlib.chdir(self.doc_path.parent):
            # Improve reproducibility, by disabling python hash seed.
            # https://stackoverflow.com/questions/52044045/os-environment-variable-reading-in-a-spawned-process
            # https://docs.python.org/3/library/multiprocessing.html#multiprocessing-start-methods
            os.environ["PYTHONHASHSEED"] = "0"
            ctx = multiprocessing.get_context("spawn")
            queue: Queue = ctx.Queue()
            process: Process = ctx.Process(  # type: ignore
                target=compile_file,
                args=(
                    self.doc_path,
                    self.number_of_documents,
                    queue,
                ),
            )
            # Share process with main thread, to enable user to kill it if needed.
            # This may prove useful if there is an infinite loop in user code
            # for example.
            self.process_started.emit(ProcessInfo(process, queue))
            process.start()
            print(f"Waiting for process {process.pid}")
            # Do *NOT* join process while there is still data in the queue.
            # See multiprocessing documentation concerning potential resulting deadlocks, and also:
            # https://stackoverflow.com/questions/31665328/python-3-multiprocessing-queue-deadlock-when-calling-join-before-the-queue-is-em
            # process.join()  <- So, don't do this!
            print(f"End of process {process.pid}")
        match queue.get():
            case MultipleFilesCompilationInfo() as info:
                return_data["compilation_info"] = info
            case BaseException() as e:
                return_data["error"] = e
            case None:
                print("Queue value is `None`: the process was most probably aborted...")
                return_data["error"] = PtyxDocumentCompilationError("compilation interrupted.")
            case other:
                raise ValueError(f"Unrecognized data: {other}")
        print("Process data successfully recovered.")

        return return_data
