from PyQt6.QtWidgets import QWidget, QVBoxLayout
from ptyx_mcq_editor.editor_widget import EditorWidget


class EditorTab(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.editor = EditorWidget(self)
        self.layout.addWidget(self.editor)
