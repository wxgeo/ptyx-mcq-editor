from PyQt6.QtWidgets import QWidget, QVBoxLayout
from ptyx_mcq_editor.settings import Document

from ptyx_mcq_editor.editor.editor_widget import EditorWidget


class EditorTab(QWidget):
    def __init__(self, parent: QWidget, doc: Document, content: str = ""):
        super().__init__(parent)
        self.doc = doc
        self.inner_layout = QVBoxLayout(self)
        self.editor = EditorWidget(self)
        self.inner_layout.addWidget(self.editor)
