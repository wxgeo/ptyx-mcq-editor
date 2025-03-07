import os
import time
import typing
import webbrowser
from pathlib import Path
from typing import cast, TYPE_CHECKING

import psutil
from PyQt6.QtCore import QThread
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QToolBar, QSpinBox, QLabel, QPushButton, QWidget, QProgressBar
from ptyx.compilation import CompilationProgress, CompilationState

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget
from ptyx_mcq_editor.publish.compiler import CompilerWorker, ProcessInfo, CompilerWorkerInfo

if typing.TYPE_CHECKING:
    from ptyx_mcq_editor.main_window import McqEditorMainWindow


class PublishToolBar(QToolBar, EnhancedWidget):
    def __init__(self, parent: "McqEditorMainWindow"):
        super().__init__(parent)
        self.compilation_is_running = False
        self.current_process_info: ProcessInfo | None = None
        self.last_compiled_doc_path: Path | None = None
        # -----------
        #   Widgets
        # ===========
        self.addWidget(QLabel("Number of documents: ", self))
        self.spinbox = QSpinBox(self)
        self.spinbox.setAccelerated(True)
        self.spinbox.setMinimum(1)
        self.spinbox.setMaximum(1000)
        self.addWidget(self.spinbox)
        # Use an empty QLabel() as spacer.
        self.addWidget(QLabel())
        # Is there any better solution?
        # Using `margin-right:10px` in spinbox stylesheet seemed to work
        # at first glance, but causes a bug in Spinbox (a shift between
        # -/+ arrows positions and the areas sensitive to clicks).
        # self.action_generate = QAction("Generate", self)
        # font = QFont()
        # font.setWeight(QFont.Weight.Bold)
        # self.action_generate.setFont(font)
        # self.addAction(self.action_generate)
        # self.action_generate.triggered.connect(self.publish)
        self.generate_doc_button = QPushButton(self)
        self.generate_doc_button.setText("Generate")
        self.generate_doc_button.setStyleSheet("font-weight: bold")
        self.addWidget(self.generate_doc_button)
        # noinspection PyUnresolvedReferences
        self.generate_doc_button.clicked.connect(self.publish)
        # Once again, use an empty QLabel() as spacer.
        self.addWidget(QLabel())
        self.open_doc_button = QPushButton(self)
        self.open_doc_button_action: QAction = self.addWidget(self.open_doc_button)
        assert isinstance(self.open_doc_button_action, QAction)
        self.open_doc_button.setText("Open pdf")
        # noinspection PyUnresolvedReferences
        self.open_doc_button.clicked.connect(self.open_pdf)
        self.open_doc_button_action.setVisible(False)
        # Once again, use an empty QLabel() as spacer.
        self.addWidget(QLabel())
        self.progress_bar = QProgressBar(cast(QWidget, self.parent()))
        # self.parent().statusBar().addWidget(self.progress_bar)
        self.progress_bar_action: QAction = self.addWidget(self.progress_bar)
        self.progress_bar_action.setVisible(False)
        parent.file_events_handler.ui_updated.connect(self.on_update)

    if TYPE_CHECKING:
        # Override signature of method addWidget(), which always return a QAction instance in practice.
        # noinspection PyMethodOverriding
        def addWidget(self, widget: QWidget | None) -> QAction:
            ...

    def on_update(self) -> None:
        self.setEnabled(self.main_window.settings.current_doc_path.suffix == ".ptyx")

    def publish(self) -> None:
        doc_path = self.main_window.settings.current_doc_path
        if doc_path is None:
            return
        if doc_path.suffix != ".ptyx":
            return
        if self.compilation_is_running:
            self.abort_thread()
        else:
            self._run_compilation(doc_path=doc_path, _use_another_thread=True)

    def open_pdf(self) -> None:
        if self.last_compiled_doc_path is not None:
            webbrowser.open(str(self.last_compiled_doc_path.with_suffix(".pdf")))
            # if platform.system() == "Darwin":  # macOS
            #     subprocess.call(("open", filepath))
            # elif platform.system() == "Windows":  # Windows
            #     os.startfile(filepath)
            # else:  # linux variants
            #     subprocess.call(("xdg-open", filepath))
            #

    def compilation_started(self) -> None:
        self.compilation_is_running = True
        # self.action_generate.setText("Stop")
        self.generate_doc_button.setText("Stop")
        assert self.current_process_info is None
        self.progress_bar_action.setVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(1000)
        self.main_window.statusbar.showMessage("Parsing pTyX document...")

    def compilation_ended(self) -> None:
        self.compilation_is_running = False
        self.current_process_info = None
        # self.action_generate.setText("Generate")
        self.generate_doc_button.setText("Generate")
        self.progress_bar_action.setVisible(False)
        self.open_doc_button_action.setVisible(True)

    def _set_progress(self, value: float) -> None:
        """Value must be a float between 0 and 1."""
        self.progress_bar.setValue(round(1000 * value))

    def update_progress(self, progress: CompilationProgress) -> None:
        # Empirically, add :
        #  * +15% of time to generate LaTeX code.
        #  * +5% of time for merging generated pdf.
        # So, set maximal value to <Number of documents> * 120%.

        target = progress.target
        parsing = 0.2 / target
        merging = 0.05
        compiling = 1 - parsing - merging
        match progress.state:
            case CompilationState.STARTED:
                message = "Starting compilation..."
                value = parsing
            case CompilationState.GENERATING_DOCS:
                message = f"Compiling document: {progress.compiled_pdf_docs}/{progress.target}"
                value = parsing + compiling * (
                    0.9 * progress.compiled_pdf_docs / target + 0.1 * progress.generated_latex_docs / target
                )
            case CompilationState.MERGING_DOCS:
                message = "Merging documents..."
                value = 1 - merging
            case CompilationState.COMPLETED:
                message = "Document generated successfully."
                value = 1
            case _:
                raise NotImplementedError
        self._set_progress(value)
        self.main_window.statusbar.showMessage(message)

    def _run_compilation(self, doc_path: Path, _use_another_thread=True) -> None:
        """Run the compilation process itself.

        By default, another thread is used, but for debugging, it may be useful
        to turn off multithreading, setting `_use_another_thread` to False.
        """
        # Small animation on the top of the tab, to let user know a process is running...
        self.compilation_started()
        # Store worker as attribute, or else it will be garbage-collected.
        self.worker = worker = CompilerWorker(doc_path=doc_path, number_of_documents=self.spinbox.value())
        # self.worker = worker = TestWorker()
        if _use_another_thread:
            self.current_thread = thread = QThread(self)
            worker.moveToThread(thread)
            worker.process_started.connect(self.set_current_process)
            worker.progress_update.connect(self.update_progress)
            worker.finished.connect(self.display_result)
            worker.finished.connect(thread.quit)
            worker.finished.connect(worker.deleteLater)
            # noinspection PyUnresolvedReferences
            thread.started.connect(worker.generate)
            # thread.started.connect(lambda: print("hello"))
            thread.finished.connect(thread.deleteLater)
            thread.finished.connect(self.compilation_ended)
            thread.start()
            print("started...")
        else:
            try:
                worker.finished.connect(self.display_result)
                worker.generate()
            finally:
                self.compilation_ended()

    def set_current_process(self, process: ProcessInfo):
        assert self.compilation_is_running
        self.current_process_info = process

    def abort_thread(self):
        process = self.current_process_info.process
        assert process is not None
        id_ = process.pid
        for child in psutil.Process(id_).children(recursive=True):
            child.terminate()
        time.sleep(0.2)
        for child in psutil.Process(id_).children(recursive=True):
            child.kill()
        process.terminate()
        time.sleep(0.2)
        process.kill()
        queue = self.current_process_info.queue
        assert queue is not None
        process.join()
        queue.put(None)
        print(f"Process {id_} interrupted.")
        self.current_thread.quit()
        # self.current_thread.wait()
        # self.compilation_ended()

    @property
    def log_viewer(self):
        return self.parent().compilation_tabs.log_viewer

    def display_result(self, info: CompilerWorkerInfo) -> None:
        self.log_viewer.setText(info["log"])
        self.log_viewer.write_log(info["doc_path"])
        self.last_compiled_doc_path = info["doc_path"]
        if (error := info.get("error")) is None:
            # self.update_tabs(doc_path=info["doc_path"])
            pass
            # TODO: Display some feedback to user.
        else:
            self.main_window.current_mcq_editor.display_error(error=error)
