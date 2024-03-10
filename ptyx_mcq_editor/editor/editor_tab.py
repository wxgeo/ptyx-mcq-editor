from typing import Final

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

from ptyx_mcq_editor.settings import Document

from ptyx_mcq_editor.editor.editor_widget import EditorWidget, Marker


class EditorTab(EnhancedWidget):
    def __init__(self, parent: QWidget, doc: Document, content: str = None):
        super().__init__(parent)
        self.doc: Final[Document] = doc
        self.inner_layout = QVBoxLayout(self)
        self.editor = EditorWidget(self)
        self.inner_layout.addWidget(self.editor)
        self.reload(content=content)
        self.connect_signals()

    def reload(self, content: str = None, preserve_history=False):
        """Reload file content from disk. History is not preserved by default."""
        path = self.doc.path
        if content is None:
            content = path.read_text(encoding="utf-8") if path is not None else ""
        lines = content.split("\n")
        new_index: list[int] = []
        for i, line in enumerate(lines):
            if line.startswith("@new: -- "):
                lines[i] = line[6:]
                new_index.append(i)
        content = "\n".join(lines)
        self.editor.setText(content, preserve_history=preserve_history)
        # Markers must be added *after* using setText().
        for i in new_index:
            self.editor.markerAdd(i, Marker.NEW)

    def connect_signals(self):
        self.editor.selectionChanged.connect(self.main_window.search_dock.highlight_all_find_results)
        # If the cursor position change, we must start a new search from this new cursor position.
        self.editor.cursorPositionChanged.connect(self.main_window.search_dock.reset_search)

        handler = self.main_window.file_events_handler
        # Save states
        self.editor.SCN_SAVEPOINTREACHED.connect(
            lambda: handler.change_doc_state(doc=self.doc, is_saved=True)
        )
        self.editor.SCN_SAVEPOINTLEFT.connect(lambda: handler.change_doc_state(doc=self.doc, is_saved=False))
