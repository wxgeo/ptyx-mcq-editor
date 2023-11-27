from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from ptyx_mcq_editor.editor.editor_tab import EditorTab

from ptyx_mcq_editor.settings import Side, Document

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

if TYPE_CHECKING:
    from ptyx_mcq_editor.main_window import McqEditorMainWindow


class FilesBook(QtWidgets.QTabWidget, EnhancedWidget):
    side: Side

    def __init__(self, parent: "McqEditorMainWindow") -> None:
        super().__init__(parent)
        self.setDocumentMode(True)
        self.setTabBarAutoHide(True)
        self.setTabsClosable(True)
        self.setMovable(True)

    def finish_initialization(self, side: Side):
        self.side = side

        handler = self.main_window.file_events_handler
        self.tabCloseRequested.connect(lambda index: handler.close_doc(side=side, index=index))
        self.currentChanged.connect(lambda index: handler.on_tab_selected(side=side, index=index))

        # TODO: For drag-and-dropping a tab from one widget to another one:
        #  https://forum.qt.io/topic/67542/drag-tabs-between-qtabwidgets/5

        def move_doc(old_index: int, new_index: int) -> None:
            handler.on_tab_moved(side, old_index, side, new_index)

        self.tabBar().tabMoved.connect(move_doc)  # type: ignore

    # noinspection PyMethodOverriding
    def dragEnterEvent(self, event: QDragEnterEvent | None) -> None:
        assert event is not None
        mime_data = event.mimeData()
        assert mime_data is not None
        if mime_data.hasUrls():
            if any(url.path().endswith(".ex") for url in mime_data.urls()):
                event.accept()
            else:
                event.ignore()
        else:
            event.ignore()

    # noinspection PyMethodOverriding
    def dropEvent(self, event: QDropEvent | None) -> None:
        assert event is not None
        mime_data = event.mimeData()
        assert mime_data is not None
        assert mime_data.hasUrls()
        self.main_window.file_events_handler.open_doc(
            paths=[Path(url.toLocalFile()) for url in mime_data.urls()]
        )

    # @property
    # def settings(self):
    #     return self.main_window.settings

    # def new_file(self) -> None:
    #     if self.ask_for_saving_if_needed():
    #         self.current_mcq_editor.setText("")
    #         self.settings.current_file = Path()
    #         self.mark_as_saved()
    #     else:
    #         print("new_file action canceled.")

    # def open_file(self, *, path: str | Path | None = None) -> None:
    #     if self.ask_for_saving_if_needed():
    #         if path is None:
    #             # noinspection PyTypeChecker
    #             path, _ = QFileDialog.getOpenFileName(
    #                 self,
    #                 "Open MCQ file",
    #                 str(self.settings.current_dir),
    #                 ";;".join(FILES_FILTER),
    #                 FILES_FILTER[0],
    #             )
    #         if path:
    #             self.settings.current_file = path  # type: ignore
    #             self.current_mcq_editor.set_saved_state(True)
    #             with open(path, encoding="utf8") as f:
    #                 self.current_mcq_editor.setText(f.read())
    #             self.mark_as_saved()
    #         else:
    #             print("open_file action canceled.")
    #     else:
    #         print("open_file action canceled.")

    #
    # def mark_as_saved(self) -> None:
    #     self.current_mcq_editor.is_saved = True

    def new_tab(self, doc: Document, index: int = None) -> None:
        if index is None:
            index = self.count()
        self.insertTab(index, EditorTab(self, doc), doc.title)
        # self.setCurrentIndex(self.count() - 1)

    def close_tab(self, index: int) -> None:
        widget = self.widget(index)
        if widget is not None and widget.close():
            self.removeTab(index)
            widget.destroy()
