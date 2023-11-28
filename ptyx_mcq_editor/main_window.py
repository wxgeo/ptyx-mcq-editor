#!/usr/bin/python3
import shutil
from pathlib import Path
from tempfile import mkdtemp

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import QMainWindow, QMessageBox

from ptyx_mcq_editor.editor.editor_widget import EditorWidget
from ptyx_mcq_editor.file_events_handler import FileEventsHandler
from ptyx_mcq_editor.generated_ui.main_ui import Ui_MainWindow
from ptyx_mcq_editor.param import ICON_PATH
from ptyx_mcq_editor.settings import Settings, Side
from ptyx_mcq_editor.tools import install_desktop_shortcut


class McqEditorMainWindow(QMainWindow, Ui_MainWindow):
    session_should_be_restored = pyqtSignal(name="session_should_be_restored")

    def __init__(self) -> None:
        super().__init__(parent=None)
        self.settings = Settings()
        self.file_events_handler = FileEventsHandler(self)
        self.setupUi(self)
        self.books = {Side.LEFT: self.left_tab_widget, Side.RIGHT: self.right_tab_widget}
        for side, book in self.books.items():
            book.finish_initialization(side=side)

        # -----------------
        # Internal settings
        # -----------------
        self.tmp_dir = Path(mkdtemp(prefix="mcq-editor-"))
        print("created temporary directory", self.tmp_dir)
        # self.ui_updates_enabled = True

        # -----------------
        # Customize display
        # -----------------
        if not ICON_PATH.is_file():
            print(f"File not found: {ICON_PATH}")
        else:
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.search_dock.setVisible(False)

        # TODO: enable right view
        self.hide_right_view()

        # -------------------
        #   Connect signals
        # -------------------
        self.connect_menu_signals()
        self.search_dock.connect_signals()

        self.session_should_be_restored.connect(self.file_events_handler.restore_previous_session)
        self.session_should_be_restored.emit()

    def connect_menu_signals(self) -> None:
        self.action_New.triggered.connect(lambda: self.file_events_handler.new_doc(side=None))
        self.action_Open.triggered.connect(lambda: self.file_events_handler.open_doc(side=None))
        self.action_Save.triggered.connect(lambda: self.file_events_handler.save_doc(side=None, index=None))
        self.action_Close.triggered.connect(lambda: self.file_events_handler.close_doc(side=None, index=None))

        self.actionSave_as.triggered.connect(
            lambda: self.file_events_handler.save_doc_as(side=None, index=None)
        )
        self.action_LaTeX.triggered.connect(self.compilation_tabs.display_latex)
        self.action_Pdf.triggered.connect(self.compilation_tabs.display_pdf)
        self.action_Add_MCQ_Editor_to_start_menu.triggered.connect(self.add_desktop_menu_entry)
        self.actionFind.triggered.connect(
            lambda: self.search_dock.toggle_find_and_replace_dialog(replace=False)
        )
        self.actionReplace.triggered.connect(
            lambda: self.search_dock.toggle_find_and_replace_dialog(replace=True)
        )
        self.menuFichier.aboutToShow.connect(self.update_recent_files_menu)
        self.action_Send_Qscintilla_Command.triggered.connect(self.dbg_send_scintilla_command)

    # noinspection PyMethodOverriding
    def closeEvent(self, event: QCloseEvent | None) -> None:
        assert event is not None
        assert self is not None
        if self.request_to_close():
            event.accept()
        else:
            event.ignore()

    @property
    def current_mcq_editor(self) -> EditorWidget | None:
        side = self.settings.current_side
        current_book = self.books[side]
        current_tab = current_book.currentWidget()
        return None if current_tab is None else current_tab.editor

    def hide_right_view(self) -> None:
        self.right_tab_widget.hide()

    def request_to_close(self) -> bool:
        if self.file_events_handler.ask_for_saving_if_needed():
            self.settings.save_settings()
            shutil.rmtree(self.tmp_dir)
            return True
        return False

    # noinspection PyDefaultArgument
    def update_recent_files_menu(self) -> None:
        recent_files = tuple(self.settings.recent_files)
        if not recent_files:
            self.menu_Recent_Files.menuAction().setVisible(False)
        else:
            self.menu_Recent_Files.clear()
            for recent_file in recent_files:
                action = self.menu_Recent_Files.addAction(recent_file.name)
                # This is tricky.
                # 1. Function provided must not use `recent_file` as unbound variable,
                # since its value will change later in this loop.
                # So, we use a default argument as a trick to copy current `recent_file` value
                # (and not a reference) inside the function.
                # 2. PyQt pass to given slot a boolean value (what is its meaning ??) if (and only if)
                # it detects that the function have at least one argument.
                # So, we have to provide a first dummy argument to the following lambda function.
                action.triggered.connect(
                    lambda _, paths=[recent_file]: self.file_events_handler.open_doc(
                        side=None, paths=list(paths)
                    )
                )
            self.menu_Recent_Files.menuAction().setVisible(True)

    def add_desktop_menu_entry(self) -> None:
        completed_process = install_desktop_shortcut()
        if completed_process.returncode == 0:
            # noinspection PyTypeChecker
            QMessageBox.information(
                self, "Shortcut installed", "This application was successfully added to start menu."
            )
        else:
            # noinspection PyTypeChecker
            QMessageBox.critical(self, "Unable to install shortcut", completed_process.stdout)

    def dbg_send_scintilla_command(self):
        if self.current_mcq_editor is not None:
            self.current_mcq_editor.dbg_send_scintilla_command()
