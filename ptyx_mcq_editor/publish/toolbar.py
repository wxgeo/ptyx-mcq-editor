from pathlib import Path


from PyQt6.QtCore import QThread
from PyQt6.QtWidgets import QToolBar, QSpinBox, QLabel, QPushButton, QWidget

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget
from ptyx_mcq_editor.publish.compiler import CompilerWorker, ProcessInfo, CompilerWorkerInfo


class PublishToolBar(QToolBar, EnhancedWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.addWidget(QLabel("Number of documents: ", self))
        self.spinbox = QSpinBox(self)
        self.spinbox.setAccelerated(True)
        self.spinbox.setMinimum(1)
        self.spinbox.setMaximum(1000)
        self.addWidget(self.spinbox)
        self.spinbox.setStyleSheet("margin-right:10px")
        # self.action_generate = QAction("Generate", self)
        # font = QFont()
        # font.setWeight(QFont.Weight.Bold)
        # self.action_generate.setFont(font)
        # self.addAction(self.action_generate)
        # self.action_generate.triggered.connect(self.publish)
        self.generate_docs_button = QPushButton(self)
        self.generate_docs_button.setText("Generate")
        self.generate_docs_button.setStyleSheet("font-weight: bold")
        self.addWidget(self.generate_docs_button)
        # noinspection PyUnresolvedReferences
        self.generate_docs_button.clicked.connect(self.publish)
        # noinspection PyUnresolvedReferences
        self.compilation_is_running = False
        self.current_process_info: ProcessInfo | None = None

    def publish(self):
        doc = self.main_window.settings.current_doc
        if doc is None:
            return
        doc_path = doc.path
        if doc_path is None:
            return
        if doc_path.suffix != ".ptyx":
            return
        if self.compilation_is_running:
            return
        self._run_compilation(doc_path=doc_path, _use_another_thread=True)

    def compilation_started(self):
        self.compilation_is_running = True
        # self.action_generate.setText("Stop")
        self.generate_docs_button.setText("Stop")
        assert self.current_process_info is None

    def compilation_ended(self):
        self.compilation_is_running = False
        self.current_process_info = None
        # self.action_generate.setText("Generate")
        self.generate_docs_button.setText("Generate")

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
        if (error := info.get("error")) is None:
            # self.update_tabs(doc_path=info["doc_path"])
            pass
            # TODO: Display some feedback to user.
        else:
            self.main_window.current_mcq_editor.display_error(error=error)
