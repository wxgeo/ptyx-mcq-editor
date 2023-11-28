from PyQt6.QtWidgets import QWidget, QVBoxLayout
from ptyx_mcq_editor.settings import Document

from ptyx_mcq_editor.editor.editor_widget import EditorWidget


class EditorTab(QWidget):
    def __init__(self, parent: QWidget, doc: Document, content: str = None):
        super().__init__(parent)
        self.doc = doc
        self.inner_layout = QVBoxLayout(self)
        if content is None:
            content = doc.path.read_text(encoding="utf-8") if doc.path is not None else ""
        self.editor = EditorWidget(self, content=content)
        self.inner_layout.addWidget(self.editor)
