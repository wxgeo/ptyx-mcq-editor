import io
import sys
from functools import wraps
from pathlib import Path
from types import TracebackType
from typing import Type, Callable

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtWidgets import QTabWidget, QDockWidget, QWidget
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

    @capture_log
    def _generate(self, doc_path: Path, target_widget: QWidget) -> None:
        self.dock.show()
        self.setCurrentIndex(self.indexOf(target_widget))
        try:
            self.start_tab_animation(self.indexOf(target_widget))
            self.latex_viewer.generate_latex(doc_path=doc_path)
            if target_widget is self.pdf_viewer:
                self.pdf_viewer.generate_pdf(doc_path=doc_path)
        finally:
            # Don't store `self.indexOf(self.pdf_viewer)`, since user may have clicked
            # on another tab in the while. It's safer to recalculate the index.
            self.stop_tab_animation(self.indexOf(target_widget))

    def update_tabs(self) -> None:
        self.latex_viewer.load()
        self.pdf_viewer.load()
        self.log_viewer.load()
