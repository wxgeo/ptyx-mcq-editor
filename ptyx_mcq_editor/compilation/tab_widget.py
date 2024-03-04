from dataclasses import dataclass
from multiprocessing import Process
from pathlib import Path

from PyQt6.QtCore import QTimer, QThread
from PyQt6.QtGui import QIcon, QContextMenuEvent, QAction
from PyQt6.QtWidgets import QTabWidget, QDockWidget, QWidget, QMenu

from ptyx_mcq_editor.compilation.compiler import CompilerWorker, CompilerWorkerInfo
from ptyx_mcq_editor.compilation.log_viewer import LogViewer

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

from ptyx_mcq_editor.compilation.pdf_viewer import PdfViewer

from ptyx_mcq_editor.compilation.latex_viewer import LatexViewer
from ptyx_mcq_editor.param import RESSOURCES_PATH


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


@dataclass(frozen=True)
class CurrentCompilationInfo:
    """Information concerning current running compilation, if any."""

    is_running: bool
    process: Process | None = None
    target: QWidget = None


class CompilationTabs(QTabWidget, EnhancedWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)
        self.latex_viewer = LatexViewer(self)
        self.pdf_viewer = PdfViewer(self)
        self.log_viewer = LogViewer(self)
        self.addTab(self.latex_viewer, "LaTeX Code")
        self.addTab(self.pdf_viewer, "Pdf Rendering")
        self.addTab(self.log_viewer, "Log message")
        # TODO: use a custom data class to gather all information concerning current running compilation
        self.running_compilation_info = CurrentCompilationInfo(is_running=False)
        # self.running_compilation = False
        # self.running_process: Process | None = None
        # `_current_animations` stores the indexes of the tabs having a running animation.
        # For each tab's index, stores the index of the animation's current frame.
        # This is used when a document is loaded.
        self._document_loading_animations = {index: Animation(self, index) for index in range(2)}

    def compilation_started(self, widget: QWidget) -> None:
        self.running_compilation_info = CurrentCompilationInfo(is_running=True, target=widget)
        self._document_loading_animations[self.indexOf(widget)].start()

    def compilation_ended(self) -> None:
        widget = self.running_compilation_info.target
        assert widget is not None
        self.running_compilation_info = CurrentCompilationInfo(is_running=False)
        self._document_loading_animations[self.indexOf(widget)].stop()

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

    def _generate(self, doc_path: Path, target_widget: QWidget) -> None:
        pdf = target_widget is self.pdf_viewer
        code = self.current_code if doc_path is None else doc_path.read_text(encoding="utf8")
        doc_path = self.current_path if doc_path is None else doc_path
        if doc_path is None:
            return
        self.dock.show()
        self.setCurrentIndex(self.indexOf(target_widget))
        # Set `_use_another_thread` to `False` to make debugging easier.
        if not self.running_compilation_info.is_running:
            self._run_compilation(
                code=code,
                doc_path=doc_path,
                tmp_dir=self.main_window.tmp_dir,
                target_widget=target_widget,
                pdf=pdf,
                _use_another_thread=True,
            )

        # self.latex_viewer.generate_latex(doc_path=doc_path)
        # if target_widget is self.pdf_viewer:
        #     self.pdf_viewer.generate_pdf(doc_path=doc_path)

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
        # Small animation on the top of the tab, to let user know a process is running...
        self.compilation_started(target_widget)
        # Store worker as attribute, or else it will be garbage-collected.
        self.worker = worker = CompilerWorker(code=code, doc_path=doc_path, tmp_dir=tmp_dir, pdf=pdf)
        # self.worker = worker = TestWorker()
        if _use_another_thread:
            self.thread = thread = QThread(self)
            worker.moveToThread(thread)
            worker.process_started.connect(self.set_current_process)
            worker.finished.connect(self.display_result)
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            thread.started.connect(worker.generate)
            # thread.started.connect(lambda: print("hello"))
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(lambda: self.compilation_ended())
            thread.start()
            print("started...")
        else:
            try:
                worker.finished.connect(self.display_result)
                worker.generate()
            finally:
                # Don't store `self.indexOf(self.pdf_viewer)`, since user may have clicked
                # on another tab in the while. It's safer to recalculate the index.
                self.compilation_ended()

    def set_current_process(self, process: Process):
        assert self.running_compilation_info.is_running
        target = self.running_compilation_info.target
        assert target is not None
        self.running_compilation_info = CurrentCompilationInfo(
            is_running=True, process=process, target=target
        )

    def abort_thread(self):
        process = self.running_compilation_info.process
        assert process is not None
        id_ = process.pid
        process.kill()
        print(f"Process {id_} interrupted.")
        self.thread.quit()
        # self.thread.wait()
        self.compilation_ended()

    def display_result(self, info: CompilerWorkerInfo) -> None:
        if (error := info.get("error")) is None:
            self.update_tabs()
        else:
            self.main_window.current_mcq_editor.editor.display_error(code=info["code"], error=error)

    def update_tabs(self) -> None:
        self.latex_viewer.load()
        self.pdf_viewer.load()
        self.log_viewer.load()

    # def mousePressEvent(self, event: QMouseEvent) -> None:
    #     if event.button() == Qt.MouseButton.RightButton:
    #         # emit customContextMenuRequested(event.pos());
    #         if self.running_compilation:
    #             print("ok!")
    #     else:
    #         super().keyPressEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        if self.running_compilation_info.is_running:
            menu = QMenu(self)
            abort = QAction("&Abort running compilation", self)
            menu.addAction(abort)
            abort.triggered.connect(self.abort_thread)
            menu.exec(event.globalPos())
