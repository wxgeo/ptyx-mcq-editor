from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6 import QtWidgets
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QCloseEvent
from PyQt6.QtWidgets import QMessageBox, QFileDialog

from ptyx_mcq_editor.settings import Side

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

if TYPE_CHECKING:
    from ptyx_mcq_editor.main_window import McqEditorMainWindow, FILES_FILTER


class FilesBook(QtWidgets.QTabWidget, EnhancedWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window: McqEditorMainWindow = self.get_main_window()
        self.side: Side

        self.setDocumentMode(True)
        self.setTabBarAutoHide(True)
        self.setTabsClosable(True)
        self.setMovable(True)

        self.tabCloseRequested.connect(self.close_tab)

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
        # TODO: for now, only one file can be opened at a time.
        for url in mime_data.urls():
            if url.path().endswith(".ex"):
                self.open_file(path=url.toLocalFile())

    # noinspection PyMethodOverriding
    def closeEvent(self, event: QCloseEvent | None) -> None:
        assert event is not None
        assert self is not None
        if self.request_to_close():
            event.accept()
        else:
            event.ignore()

    @property
    def settings(self):
        return self.main_window.settings

    def new_file(self) -> None:
        if self.ask_for_saving_if_needed():
            self.mcq_editor.setText("")
            self.settings.current_file = Path()
            self.mark_as_saved()
        else:
            print("new_file action canceled.")

    def open_file(self, *, path: str | Path | None = None) -> None:
        if self.ask_for_saving_if_needed():
            if path is None:
                # noinspection PyTypeChecker
                path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Open MCQ file",
                    str(self.settings.current_dir),
                    ";;".join(FILES_FILTER),
                    FILES_FILTER[0],
                )
            if path:
                self.settings.current_file = path  # type: ignore
                self.current_mcq_editor.set_saved_state(True)
                with open(path, encoding="utf8") as f:
                    self.mcq_editor.setText(f.read())
                self.mark_as_saved()
            else:
                print("open_file action canceled.")
        else:
            print("open_file action canceled.")

    def save_file_as(self, *, path: str | Path | None = None) -> None:
        if path is None:
            # noinspection PyTypeChecker
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save as...",
                str(self.settings.current_file),
                ";;".join(FILES_FILTER),
                FILES_FILTER[0],
            )
        if path:
            self.settings.current_file = path  # type: ignore
            with open(path, "w", encoding="utf8") as f:
                f.write(self.mcq_editor.text())
            self.mark_as_saved()
        else:
            print("save_file action canceled.")

    def save_file(self) -> None:
        self.save_file_as(path=self.settings.current_file)

    def ask_for_saving_if_needed(self) -> bool:
        """Ask user what to do if file is not saved.

        Return `False` if user discard operation, else `True`."""
        if self.current_file_saved:
            return True
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Unsaved document")
        dialog.setText("Save the document before closing it ?")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Abort
        )
        dialog.setDefaultButton(QMessageBox.StandardButton.Save)
        dialog.exec()
        result = dialog.result()
        if result == QMessageBox.StandardButton.Save:
            self.save_file()
        return result != QMessageBox.StandardButton.Abort

    def mark_as_saved(self) -> None:
        self.current_mcq_editor.is_saved = True

    def close_tab(self, index: int) -> None:
        print(f"closing tab {index}")
        self.settings.close_doc(index)
        widget = self.widget(index)
        if widget is not None and widget.close():
            self.removeTab(index)
            widget.destroy()
