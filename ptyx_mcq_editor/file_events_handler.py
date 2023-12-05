from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Final, Sequence, Callable

from PyQt6.Qsci import QsciScintilla
from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QDialog, QDialogButtonBox
from ptyx_mcq.cli import get_template_path, update_include

from ptyx_mcq_editor.editor.editor_tab import EditorTab
from ptyx_mcq_editor.editor.editor_widget import EditorWidget
from ptyx_mcq_editor.generated_ui import ask_for_saving_ui
import ptyx_mcq_editor.param as param
from ptyx_mcq_editor.settings import Document, Settings, Side, DocumentHasNoPath, SamePath

if TYPE_CHECKING:
    from ptyx_mcq_editor.main_window import McqEditorMainWindow
    from ptyx_mcq_editor.files_book import FilesBook

Abort = QMessageBox.StandardButton.Abort
Discard = QMessageBox.StandardButton.Discard
Save = QMessageBox.StandardButton.Save

FILES_FILTER = ("Mcq Exercises Files (*.ex)", "pTyX Files (*.ptyx)", "All Files (*.*)")


def update_ui(f: Callable[..., bool]) -> Callable[..., bool]:
    """Decorator used to indicate that UI must be updated if the operation was successful.

    The decorated function must return True if the operation was successful, False else.

    When nested operations are performed, intermediate ui updates are prevented by
    freezing temporally the user interface, then updating it only once the last operation is performed.
    """

    @wraps(f)
    def wrapper(self: "FileEventsHandler", *args, **kw) -> bool:
        current_freeze_value = self.freeze_update_ui
        self.freeze_update_ui = True
        if not param.DEBUG:
            self.main_window.setUpdatesEnabled(False)
        try:
            if param.DEBUG:
                _args = [repr(arg) for arg in args] + [f"{key}={val!r}" for (key, val) in kw.items()]
                print(f"{f.__name__}({', '.join(_args)})")
            else:
                print(f.__name__)
            update = f(self, *args, **kw)
            assert isinstance(update, bool), update
            if update and not current_freeze_value:
                self._update_ui()
            return update
        finally:
            self.main_window.setUpdatesEnabled(True)
            self.freeze_update_ui = current_freeze_value

    return wrapper


class AskForSavingDialog(QDialog, ask_for_saving_ui.Ui_Dialog):
    CANCEL = 0
    SAVE = 1
    DISCARD = 2

    def __init__(self, parent: "McqEditorMainWindow", unsaved_filenames: list[str]) -> None:
        super().__init__(parent=parent)
        self.setupUi(self)
        self.unsaved_filenames = unsaved_filenames
        self.listWidget.addItems(unsaved_filenames)
        for i in range(self.listWidget.count()):
            item = self.listWidget.item(i)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)

        self.buttonBox.button(QDialogButtonBox.StandardButton.Discard).clicked.connect(
            lambda: self.done(self.DISCARD)
        )


class FileEventsHandler(QObject):
    def __init__(self, main_window: "McqEditorMainWindow"):
        super().__init__(parent=main_window)
        self.main_window: Final = main_window
        self.freeze_update_ui: bool = False  # See update_ui() decorator docstring.

    @update_ui
    def finalize(self, paths: Sequence[Path] = ()) -> bool:
        if paths:
            self.settings.new_session()
            self.open_doc(paths=paths)
        return True

    # ---------------------
    #      Shortcuts
    # =====================

    @property
    def settings(self):
        return self.main_window.settings

    def book(self, side: Side | None) -> "FilesBook":
        if side is None:
            side = self.settings.current_side
        return self.main_window.books[side]

    # ------------------------------------------
    #      UI synchronization with settings
    # ==========================================

    def _update_ui(self) -> None:
        """Update window and tab titles according to settings data.

        Assure synchronization between ui and settings."""
        for side in Side:
            docs = self.settings.docs(side)
            tabs = self.book(side)
            tab_bar = tabs.tabBar()
            # print(f"Before: {side}: {docs.current_index=}, {len(docs)=}")
            assert tab_bar is not None
            # Synchronize tabs with docs, starting from the first doc.
            # 1. For each document, if `i` is its position:
            #    Test if there is a tab at a position `j >= i` corresponding to it.
            #       - If `j == i`, nothing to do.
            #       - If `j > i`, move tab from `j` to `i`.
            #       - If there is no such tab, create it at position `i`.
            # 2. When all docs have been handled, all remaining tabs must be removed.
            # 3. Finally, set the index of the current tab to match the current document.
            for i, doc in enumerate(docs):
                # Assertion for step `i`: the docs and tabs are synchronized until index `i-1`.
                for j in range(i, tabs.count()):
                    widget = tabs.widget(j)
                    assert isinstance(widget, EditorTab)
                    if widget.doc is doc:
                        if j != i:
                            # Move matching tab to index i.
                            tab_bar.moveTab(j, i)
                        break
                else:
                    tabs.new_tab(doc, index=i)
                tabs.setTabText(i, doc.title)
            # Remove any remaining tab.
            for j in range(tabs.count() - 1, len(docs) - 1, -1):
                widget = tabs.widget(j)
                tabs.removeTab(j)
                widget.destroy()

            # Update current index.
            if len(docs) > 0:
                current_index = docs.current_index
                if param.DEBUG:
                    print(f"{side}: {docs.current_index=}")
                assert current_index is not None
                tabs.setCurrentIndex(current_index)

            else:
                if param.DEBUG:
                    print(f"{side}: no document to select.")
        if len(docs := self.settings.docs()) > 0:
            self.main_window.setWindowTitle(f"{param.WINDOW_TITLE} - {docs.current_doc.title}")
        else:
            self.main_window.setWindowTitle(param.WINDOW_TITLE)

    # ----------------------------------------------
    #      Settings synchronization on events
    # ==============================================

    def on_tab_selected(self, side: Side, index: int) -> None:
        if not self.freeze_update_ui:
            if param.DEBUG:
                print(f"tab_selected: {side}:{index}")
            self.settings.docs(side).current_index = index
            self._update_ui()
            self.main_window.compilation_tabs.update_tabs()

    def on_tab_moved(
        self, old_side: Side, old_index: int, new_side: Side = None, new_index: int = None
    ) -> None:
        if param.DEBUG:
            print(f"tab_moved: {old_side}:{old_index} -> {new_side}:{new_index}")
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

    # -------------------
    #      Actions
    # ===================

    @update_ui
    def restore_previous_session(self) -> bool:
        self.main_window.settings = Settings.load_settings()
        return True

    @update_ui
    def new_session(self) -> bool:
        self.main_window.settings.new_session()
        return True

    @update_ui
    def new_doc(self, side: Side = None, content: str = None) -> bool:
        if side is None:
            side = self.settings.current_side
        doc = self.settings.new_doc(side)
        if content:
            self.book(side).new_tab(doc, content=content)
        # try:
        #     self.book(side).new_tab(self.settings.new_doc(side))
        # except Exception as e:
        #     # TODO: Display a message
        #     raise e
        return True

    @update_ui
    def new_mcq_ptyx_doc(self, side: Side = None) -> bool:
        ptyx_paths = list(get_template_path().glob("*.ptyx"))
        if len(ptyx_paths) == 0:
            raise FileNotFoundError("No template found.")
        elif len(ptyx_paths) > 1:
            raise FileNotFoundError("Bad template: several ptyx files inside.")
        content = (ptyx_paths[0]).read_text(encoding="utf-8")
        return self.new_doc(side, content=content)

    @update_ui
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
            if not path.is_file():
                raise FileNotFoundError(f"File '{path}' does not exist.")
            try:
                doc = self.settings.docs(side).add_doc(path=path)
                # noinspection PyProtectedMember
                assert doc._is_saved
                assert doc.is_saved
            except SamePath:
                print(f"Skipping '{path}': already opened.")
                # No new file will be opened, however the selected doc may have changed.
                # So, we must return `True` in that case too to update UI.
        return True

    @update_ui
    def save_doc(self, side: Side = None, index: int = None) -> bool:
        doc = self.settings.docs(side).doc(index)
        if doc is None:
            print("No doc to save!")
            return False
        return self.save_doc_as(side, index, doc.path)

    @update_ui
    def change_doc_state(self, doc: Document, is_saved: bool) -> bool:
        doc.is_saved = is_saved
        return True

    @update_ui
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
            # Select tab, so that the user sees what he is about to save.
            self.book(side).setCurrentIndex(index)
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
                        doc.write(tab.editor.text(), path=path)
                        # Tell Scintilla that the current editor's state is its new saved state.
                        # More information on Scintilla messages: http://www.scintilla.org/ScintillaDoc.html
                        tab.editor.SendScintilla(QsciScintilla.SCI_SETSAVEPOINT)
                        saved = True
                    except (IOError, DocumentHasNoPath, SamePath) as e:
                        # TODO: Custom message
                        print(e)
                        path = None
        return saved

    @update_ui
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
        return True

    # -----------------
    #      Dialogs
    # =================

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
        unsaved_docs: dict[tuple[Side, int], str] = {
            (side, index): doc.title
            for side in Side
            for (index, doc) in enumerate(self.settings.docs(side))
            if not doc.is_saved
        }
        if len(unsaved_docs) == 0:
            return True
        dialog = AskForSavingDialog(self.main_window, list(unsaved_docs.values()))
        result = dialog.exec()
        if result == AskForSavingDialog.SAVE:
            for i, (side, index) in enumerate(unsaved_docs):
                if dialog.listWidget.item(i).checkState() == Qt.CheckState.Checked:
                    print(i, "selected")
                    if not self.save_doc(side, index):
                        return False

            print("Not Implemented.")
            return True
        elif result == AskForSavingDialog.DISCARD:
            return True
        else:
            assert result == AskForSavingDialog.CANCEL, repr(result)
            return False

    # ----------------------------
    #      Specific actions
    # ============================

    def update_ptyx_imports(self):
        if (current_doc := self.settings.docs().current_doc) is not None and self.save_doc():
            path = current_doc.path
            assert path is not None
            update_include(current_doc.path)
            widget = self.book(None).currentWidget()
            assert isinstance(widget, EditorTab), widget
            widget.reload()

    def open_file_from_current_ptyx_import_directive(
        self, current_line: int = None, background: bool = False
    ):
        if self.settings.docs().current_doc is not None:
            widget = self.book(None).currentWidget()
            assert isinstance(widget, EditorTab), widget
            if current_line is None:
                current_line = widget.editor.getCursorPosition()[0]
            print(f"Directive-open: {current_line=}")
            directory = self.settings.current_directory
            for line in range(0, current_line):
                text = widget.editor.text(line)
                pos = text.find(prefix := "-- DIR: ")
                if pos != -1:
                    directory = Path(text[pos + len(prefix) :].strip()).expanduser().resolve()
                    if param.DEBUG:
                        print(f"{directory=}")
            import_directive = widget.editor.text(current_line)
            pos = import_directive.find(prefix := "-- ")
            if pos == -1:
                raise ValueError("No directive in this line.")
            else:
                import_path = Path(import_directive[pos + len(prefix) :].strip())
                if not import_path.is_absolute():
                    import_path = directory / import_path
                current_index = self.settings.docs().current_index
                self.open_doc(paths=[import_path])
                if background:
                    self.settings.docs().current_index = current_index
                    self._update_ui()
