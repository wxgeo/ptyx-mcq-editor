import io
import sys
from functools import wraps
from pathlib import Path
from types import TracebackType
from typing import Type, Callable

from PyQt6.QtCore import QTimer, QThread
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QTabWidget, QDockWidget, QWidget

from ptyx_mcq_editor.compilation.compiler import CompilerWorker, CompilerWorkerInfo
from ptyx_mcq_editor.compilation.log_viewer import LogViewer

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

from ptyx_mcq_editor.compilation.pdf_viewer import PdfViewer

from ptyx_mcq_editor.compilation.latex_viewer import LatexViewer
from ptyx_mcq_editor.param import RESSOURCES_PATH


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


def capture_log(f: Callable) -> Callable:
    """Decorator used to capture a copy of stdout and stderr and print their content in log tab."""

    @wraps(f)
    def wrapper(self: "CompilationTabs", *args, **kw):
        if not self.log_already_captured:
            try:
                with CaptureLog() as log:
                    self.log_already_captured = True
                    f(self, *args, **kw)
                    self.log_viewer.setText(log.getvalue())
                    self.log_viewer.write_log()
            finally:
                self.log_already_captured = False

    return wrapper


class Animation:
    def __init__(self, parent: "CompilationTabs", index: int):
        self.parent = parent
        self.index = index
        self.frame: int = 0
        self.timer = QTimer(parent)
        self.timer.setInterval(70)
        self.timer.timeout.connect(self._update)

    def start(self):
        self.frame = 0
        self.timer.start()

    def stop(self):
        self.timer.stop()
        self.parent.setTabIcon(self.index, QIcon())

    def _update(self):
        self.frame = (self.frame + 1) % 24
        self.parent.setTabIcon(self.index, QIcon(str(RESSOURCES_PATH / f"wait/wait-{self.frame}.svg")))


# https://realpython.com/python-pyqt-qthread/


class CompilationTabs(QTabWidget, EnhancedWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)
        self.log_already_captured = False
        self.latex_viewer = LatexViewer(self)
        self.pdf_viewer = PdfViewer(self)
        self.log_viewer = LogViewer(self)
        self.addTab(self.latex_viewer, "LaTeX Code")
        self.addTab(self.pdf_viewer, "Pdf Rendering")
        self.addTab(self.log_viewer, "Log message")
        # `_current_animations` stores the indexes of the tabs having a running animation.
        # For each tab's index, stores the index of the animation's current frame.
        # This is used when a document is loaded.
        self._document_loading_animations = {index: Animation(self, index) for index in range(2)}

    def start_tab_animation(self, index: int) -> None:
        self._document_loading_animations[index].start()

    def stop_tab_animation(self, index: int) -> None:
        self._document_loading_animations[index].stop()

    @property
    def dock(self) -> QDockWidget:
        dock = self.parent().parent()  # type: ignore
        assert isinstance(dock, QDockWidget)
        return dock

    def generate_pdf(self, doc_path: Path = None) -> None:
        self._generate(doc_path, self.pdf_viewer)

    def generate_latex(self, doc_path: Path = None) -> None:
        self._generate(doc_path, self.latex_viewer)

    @property
    def current_code(self) -> str:
        return self.main_window.current_mcq_editor.text()

    @property
    def current_path(self) -> Path | None:
        """Return the path of the current document.

        If the current document has no path, a temporary unique name is generated.
        If there is no current document, `None` is returned instead.
        """
        doc = self.main_window.settings.current_doc
        if doc is None:
            return None
        doc_path = doc.path
        if doc_path is None:
            doc_path = Path(f"new-doc-{doc.doc_id}")
        return doc_path

    @capture_log
    def _generate(self, doc_path: Path, target_widget: QWidget) -> None:
        pdf = target_widget is self.pdf_viewer
        code = self.current_code if doc_path is None else doc_path.read_text(encoding="utf8")
        doc_path = self.current_path if doc_path is None else doc_path
        if doc_path is None:
            return
        self.dock.show()
        self.setCurrentIndex(self.indexOf(target_widget))
        try:
            self.start_tab_animation(self.indexOf(target_widget))

            # Set `_use_another_thread` to `False` to make debugging easier.
            self._run_compilation(
                code=code,
                doc_path=doc_path,
                tmp_dir=self.main_window.tmp_dir,
                target_widget=target_widget,
                pdf=pdf,
                _use_another_thread=False,
            )

            # self.latex_viewer.generate_latex(doc_path=doc_path)
            # if target_widget is self.pdf_viewer:
            #     self.pdf_viewer.generate_pdf(doc_path=doc_path)
        finally:
            # Don't store `self.indexOf(self.pdf_viewer)`, since user may have clicked
            # on another tab in the while. It's safer to recalculate the index.
            self.stop_tab_animation(self.indexOf(target_widget))

    def _run_compilation(
        self,
        code: str,
        doc_path: Path,
        tmp_dir: Path,
        pdf: bool,
        target_widget: QWidget,
        _use_another_thread=True,
    ) -> None:
        """Run the compilation process itself.

        By default, another thread is used, but for debugging, it may be useful
        to turn off multithreading, setting `_use_another_thread` to False.
        """
        worker = CompilerWorker(code=code, doc_path=doc_path, tmp_dir=tmp_dir, pdf=pdf)
        if _use_another_thread:
            thread = QThread(self)
            worker.moveToThread(thread)
            worker.finished.connect(self.display_result)
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.started.connect(worker.generate)
            thread.started.connect(lambda: print("hello"))
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(self.stop_tab_animation)
            thread.start()
        else:
            try:
                worker.finished.connect(self.display_result)
                worker.generate()
            finally:
                # Don't store `self.indexOf(self.pdf_viewer)`, since user may have clicked
                # on another tab in the while. It's safer to recalculate the index.
                self.stop_tab_animation(self.indexOf(target_widget))

    def display_result(self, info: CompilerWorkerInfo) -> None:
        print("Hello !")
        if (error := info.get("error")) is None:
            self.update_tabs()
        else:
            self.main_window.current_mcq_editor.editor.display_error(code=info["code"], error=error)

    def update_tabs(self) -> None:
        self.latex_viewer.load()
        self.pdf_viewer.load()
        self.log_viewer.load()
