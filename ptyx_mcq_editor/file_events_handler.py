from pathlib import Path

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QDialog
from ptyx_mcq_editor.editor.editor_tab import EditorTab

from ptyx_mcq_editor.editor.editor_widget import EditorWidget

from ptyx_mcq_editor.generated_ui.ask_for_saving_ui import Ui_Dialog as AskForSavingDialogUi

from ptyx_mcq_editor.settings import Document, Settings, Side, DocumentHasNoPath, SamePath
from typing import TYPE_CHECKING, Final, Sequence

if TYPE_CHECKING:
    from ptyx_mcq_editor.main_window import McqEditorMainWindow
    from ptyx_mcq_editor.files_book import FilesBook

Abort = QMessageBox.StandardButton.Abort
Discard = QMessageBox.StandardButton.Discard
Save = QMessageBox.StandardButton.Save

FILES_FILTER = ("Mcq Exercises Files (*.ex)", "pTyX Files (*.ptyx)", "All Files (*.*)")


class FileEventsHandler(QObject):
    # noinspection PyArgumentList
    new_tab = pyqtSignal(Side, Document)
    # noinspection PyArgumentList
    close_tab = pyqtSignal(Side, int)
    # noinspection PyArgumentList
    move_tab = pyqtSignal(Side, int, int)

    def __init__(self, main_window: "McqEditorMainWindow"):
        super().__init__(parent=main_window)
        self.main_window: Final = main_window
        self.settings: Final[Settings] = main_window.settings

    # @property
    # def settings(self) -> Settings:
    #     return self.main_window.settings

    def book(self, side: Side | None) -> "FilesBook":
        if side is None:
            side = self.settings.current_side
        return self.main_window.books[side]

    def new_doc(self, side: Side = None) -> bool:
        if side is None:
            side = self.settings.current_side
        try:
            self.book(side).new_tab(self.settings.new_doc(side))
        except Exception as e:
            # TODO: Display a message
            raise
        self.main_window.update_ui()
        return True

    def open_doc(self, side: Side = None, paths: Sequence[Path] = ()) -> bool:
        if len(paths) == 0:
            # noinspection PyTypeChecker
            paths = self.open_dialog()
            if len(paths) == 0:
                print("open_file action canceled.")
                return False

        if side is None:
            side = self.settings.current_side
        for path in paths:
            try:
                self.book(side).new_tab(self.settings.new_doc(side), content=path.read_text("utf-8"))
            except SamePath:
                print(f"Skipping '{path}': already opened.")
        self.main_window.update_ui()
        return True

    def save_doc(self, side: Side = None, index: int = None) -> bool:
        doc = self.settings.docs(side).doc(index)
        if doc is None:
            print("No doc to save!")
            return False
        return self.save_doc_as(side, index, doc.path)

    def select_doc(self, side: Side, index: int) -> None:
        self.settings.docs(side).current_index = index
        self.main_window.update_ui()

    def change_doc_state(self, doc: Document, is_saved: bool) -> None:
        doc.is_saved = is_saved
        self.main_window.update_ui()

    def save_doc_as(self, side: Side = None, index: int = None, path: Path = None) -> bool:
        """Save document. Return True if document was saved, else False."""
        if index is None:
            index = self.settings.docs(side).current_index
        saved = False
        if index is None:
            print("No document to save!")
        else:
            doc = self.settings.docs(side).doc(index)
            # If index is not None, doc shouldn't be either.
            assert doc is not None
            tab = self.book(side).widget(index)
            # This should hold for tab too.
            assert isinstance(tab, EditorTab)
            saved = canceled = False
            while not saved and not canceled:
                assert isinstance(tab.editor, EditorWidget)
                if path is None:
                    path = self.save_dialog()
                    if path is None:
                        # User cancelled dialog
                        print("save_file action canceled.")
                        canceled = True
                if not canceled:
                    assert path is not None
                    try:
                        self._write_content(tab.editor, doc, path)
                        saved = True
                    except (IOError, DocumentHasNoPath, SamePath) as e:
                        # TODO: Custom message
                        print(e)
            if saved:
                self.main_window.update_ui()
        return saved

    @staticmethod
    def _write_content(editor: EditorWidget, doc: Document, path: Path):
        doc.write(editor.text(), path=path)
        # Tell Scintilla that the current editor's state is its new saved state.
        # More information on Scintilla messages: http://www.scintilla.org/ScintillaDoc.html
        editor.SendScintilla(QsciScintilla.SCI_SETSAVEPOINT)

    def move_doc(self, old_side: Side, old_index: int, new_side: Side = None, new_index: int = None) -> None:
        if new_side is None:
            new_side = old_side
        if new_index is None:
            new_index = old_index
        if new_side != old_side:
            # TODO: implement this.
            raise NotImplementedError
        else:
            self.settings.move_doc(old_side, old_index, new_side, new_index)
            # Warning: no need to manually move tab, Qt will automatically do this.
            assert isinstance(tab := self.book(new_side).widget(new_index), EditorTab)
            assert self.settings.docs(new_side).doc(new_index) is tab.doc

            # self.book(new_side).move_tab(old_index, new_index)
            # self.move_tab.emit(new_side, old_index, new_index)
        print("move_doc")

    def close_doc(self, side: Side = None, index: int = None) -> bool:
        """Close given document if it is saved, else ask user what to do.

        Return True if the document was closed, False else (user aborted process)."""
        if side is None:
            side = self.settings.current_side
        if index is None:
            index = self.settings.docs(side).current_index
        if index is None:
            print("No document to close.")
        else:
            doc = self.settings.docs(side).doc(index)
            # If index is not None, doc shouldn't be either.
            assert doc is not None
            # Test document state.
            if not doc.is_saved:
                user_answer = self.should_tab_be_saved()
                if user_answer == Abort:
                    return False
                elif user_answer == Save:
                    self.save_doc(side, index)
                else:
                    assert user_answer == Discard, user_answer
            self.settings.close_doc(side, index)
            self.book(side).close_tab(index)
        self.main_window.update_ui()
        return True

    # -----------------
    #      Dialogs
    # -----------------

    def save_dialog(self) -> Path | None:
        # noinspection PyTypeChecker
        path_str, _ = QFileDialog.getSaveFileName(
            self.main_window,
            "Save as...",
            str(self.settings.current_directory),
            ";;".join(FILES_FILTER),
            FILES_FILTER[0],
        )
        if path_str == "":
            path: Path | None = None
        else:
            path = Path(path_str)
            self.settings.current_directory = path.parent
        return path

    def open_dialog(self) -> list[Path]:
        # noinspection PyTypeChecker
        filenames, _ = QFileDialog.getOpenFileNames(
            self.main_window,
            "Open MCQ or Ptyx files",
            str(self.settings.current_directory),
            ";;".join(FILES_FILTER),
            FILES_FILTER[0],
        )
        if filenames:
            self.settings.current_directory = Path(filenames[0]).parent
        return [Path(filename) for filename in filenames]

    def should_tab_be_saved(self) -> QMessageBox.StandardButton:
        """Ask user what to do if file is not saved.

        Return `False` if user discard operation, else `True`."""

        dialog = QMessageBox(self.main_window)
        dialog.setWindowTitle("Unsaved document")
        dialog.setText("Save the document before closing it ?")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setStandardButtons(Save | Discard | Abort)
        dialog.setDefaultButton(Save)
        dialog.exec()
        return dialog.result()  # type: ignore  # https://doc.qt.io/qt-6/qdialog.html#result

    def ask_for_saving_if_needed(self) -> bool:
        """Ask if all tabs should be saved, when closing program.

        Return True if we can quit program, or False is user canceled action.
        """
        unsaved: list[str] = [
            doc.title for side in Side for doc in self.settings.docs(side) if not doc.is_saved
        ]
        if len(unsaved) == 0:
            return True
        dialog = QDialog(self.main_window)
        ui = AskForSavingDialogUi()
        ui.setupUi(dialog)
        ui.listWidget.addItems(unsaved)
        for i in range(ui.listWidget.count()):
            item = ui.listWidget.item(i)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
        dialog.exec()
        result = dialog.result()
        if result == QMessageBox.StandardButton.Save:
            print("Not Implemented.")
            return False
        elif result == QMessageBox.StandardButton.Discard:
            return True
        else:
            assert result == QMessageBox.StandardButton.Abort, repr(result)
            return False
