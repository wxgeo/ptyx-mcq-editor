#!/usr/bin/python3
import re
import shutil
from functools import partial
from pathlib import Path
from tempfile import mkdtemp
from typing import Optional

import ptyx_mcq
from PyQt6 import Qsci, QtPdfWidgets
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QCloseEvent, QIcon
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QMessageBox, QDialog
from ptyx.compilation import compile_latex_to_pdf  # , _build_command
from ptyx.latex_generator import Compiler

from ptyx_mcq_editor.editor_widget import EditorWidget
from ptyx_mcq_editor.find_and_replace import SearchAction
from ptyx_mcq_editor.settings import Settings
from ptyx_mcq_editor.tools import install_desktop_shortcut
from ptyx_mcq_editor.ui import dbg_send_scintilla_messages_ui
from ptyx_mcq_editor.ui.main_ui import Ui_MainWindow

TEST = r"""
* Combien fait
...............
while True:
    let a, b, c, d in 2..9
    if distinct(a/b-c/d+S(1)/2, a/b-c/d-S(1)/2, (a+c+1)/(b+d+2), (a-c+1)/(b+d+2), (a-c+1)/(b-d+2)):
        break
...............
$\dfrac{#a}{#b}-\dfrac{#c}{#d}+\dfrac12$~?

+ $#{a/b-c/d+S(1)/2}$
- $#{a/b-c/d-S(1)/2}$
- $#{(a+c+1)/(b+d+2)}$
- $#{(a-c+1)/(b+d+2)}$
- $#{(a-c+1)/(b-d+2)}$

- aucune de ces réponses n'est correcte
"""
DEBUG = False

FILES_FILTER = ("Mcq Exercises Files (*.ex)", "All Files (*.*)")

ICON_PATH = Path(__file__).parent.parent / "ressources/mcq-editor.svg"


class McqEditorMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        super().__init__(parent=None)
        self.setupUi(self)
        # -----------------
        # Internal settings
        # -----------------
        self.current_file_saved = True
        self.tmp_dir = Path(mkdtemp(prefix="mcq-editor-"))
        self.pdf_viewer = QtPdfWidgets.QPdfView(None)
        self.pdf_doc = QPdfDocument(None)
        self.settings = Settings.load()
        # -----------------
        # Customize display
        # -----------------
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        # -------------------------------- #
        #     QScintilla editor setup      #
        # -------------------------------- #

        # ! Make instance of QSciScintilla class!
        # ----------------------------------------
        # self.mcq_editor = QsciScintilla()
        if DEBUG:
            self.mcq_editor.setText(TEST)  # 'TEST' is a string containing some pTyX-MCQ-code

        # -------------------------------- #
        #          Install lexer           #
        # -------------------------------- #

        self.latex_editor.setLexer(Qsci.QsciLexerTeX(self.latex_editor))

        self.pdf_viewer.setParent(self.pdf_tab)
        self.pdf_viewer.setObjectName("pdf_viewer")
        self.pdf_tab_grid.addWidget(self.pdf_viewer, 0, 0, 1, 1)

        self.search_dock.setVisible(False)
        self.search_dock.main_window = self

        print("created temporary directory", self.tmp_dir)

        if not ICON_PATH.is_file():
            print(f"File not found: {ICON_PATH}")
        self.update_title()

        self.hide_right_view()

        # -------------------
        #   Connect signals
        # -------------------
        # Menu
        self.action_New.triggered.connect(self.new_file)
        self.action_Open.triggered.connect(self.open_file)
        self.action_Save.triggered.connect(self.save_file)
        self.actionSave_as.triggered.connect(self.save_file_as)
        self.action_LaTeX.triggered.connect(self.display_latex)
        self.action_Pdf.triggered.connect(self.display_pdf)
        self.action_Add_MCQ_Editor_to_start_menu.triggered.connect(self.add_menu_entry)
        self.actionFind.triggered.connect(
            partial(self.search_dock.toggle_find_and_replace_dialog, replace=False)
        )
        self.actionReplace.triggered.connect(
            partial(self.search_dock.toggle_find_and_replace_dialog, replace=True)
        )
        self.menuFichier.aboutToShow.connect(self.update_recent_files_menu)
        self.action_Send_Qscintilla_Command.triggered.connect(self.dbg_send_scintilla_command)

        # Find and search dock
        func = self.search_dock.find_and_replace
        self.replace_all_button.pressed.connect(self.search_dock.replace_all)
        self.replace_button.pressed.connect(partial(func, action=SearchAction.REPLACE))
        self.next_button.pressed.connect(partial(func, action=SearchAction.FIND_NEXT))
        self.previous_button.pressed.connect(partial(func, action=SearchAction.FIND_PREVIOUS))
        self.find_field.returnPressed.connect(partial(func, action=SearchAction.FIND_NEXT))
        self.find_field.textChanged.connect(self.search_dock.search_changed)
        for box in [self.wholeCheckBox, self.regexCheckBox, self.caseCheckBox, self.selectionOnlyCheckBox]:
            box.stateChanged.connect(self.search_dock.search_changed)
        self.mcq_editor.selectionChanged.connect(self.search_dock.highlight_all_find_results)
        # If the cursor position change, we must start a new search from this new cursor position.
        self.mcq_editor.cursorPositionChanged.connect(self.search_dock.reset_search)

        # Save states
        self.mcq_editor.SCN_SAVEPOINTREACHED.connect(self._on_text_saved)
        self.mcq_editor.SCN_SAVEPOINTLEFT.connect(self._on_text_changed)

    @property
    def current_mcq_editor(self) -> EditorWidget:
        return self.mcq_editor

    def dragEnterEvent(self, event: Optional[QDragEnterEvent]) -> None:
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

    def dropEvent(self, event: Optional[QDropEvent]) -> None:
        assert event is not None
        mime_data = event.mimeData()
        assert mime_data is not None
        assert mime_data.hasUrls()
        # TODO: for now, only one file can be opened at a time.
        for url in mime_data.urls():
            if url.path().endswith(".ex"):
                self.open_file(path=url.toLocalFile())

    def closeEvent(self, event: Optional[QCloseEvent]) -> None:
        assert event is not None
        assert self is not None
        if self.request_to_close():
            event.accept()
        else:
            event.ignore()

    def hide_right_view(self):
        self.right_tab_widget.hide()

    def request_to_close(self) -> bool:
        if self.ask_for_saving_if_needed():
            self.settings.save()
            shutil.rmtree(self.tmp_dir)
            return True
        return False

    def update_recent_files_menu(self) -> None:
        if not self.settings.recent_files:
            self.menu_Recent_Files.menuAction().setVisible(False)
        else:
            self.menu_Recent_Files.clear()
            for recent_file in self.settings.recent_files:
                if recent_file.is_file():
                    action = self.menu_Recent_Files.addAction(recent_file.name)
                    action.triggered.connect(partial(self.open_file, path=recent_file))
            self.menu_Recent_Files.menuAction().setVisible(True)

    def _get_latex(self) -> str:
        template = (Path(ptyx_mcq.__file__).parent / "templates/original/new.ptyx").read_text()
        content = self.mcq_editor.text()
        if not content.lstrip().startswith("* "):
            content = "* \n" + content
        # re.sub() doesn't seem to work when "\dfrac" is in the replacement string... using re.split() instead.
        before, _, after = re.split("(<<<.+>>>)", template, flags=re.MULTILINE | re.DOTALL)
        ptyx_code = f"{before}\n<<<\n{content}\n>>>\n{after}"
        compiler = Compiler()
        latex = compiler.parse(
            code=ptyx_code, MCQ_KEEP_ALL_VERSIONS=True, PTYX_WITH_ANSWERS=True, MCQ_REMOVE_HEADER=True
        )
        return latex

    def display_latex(self) -> None:
        self.latex_editor.setText(self._get_latex())
        self.tabWidget.setCurrentIndex(0)

    def display_pdf(self) -> None:
        self.latex_editor.setText(latex := self._get_latex())
        (latex_file := self.tmp_dir / "tmp.tex").write_text(latex)
        pdf_file = self.tmp_dir / "tmp.pdf"
        # print(_build_command(latex_file, pdf_file))
        compilation_info = compile_latex_to_pdf(latex_file, dest=self.tmp_dir)
        self.pdf_doc.setParent(self.pdf_viewer)
        self.pdf_doc.load(str(pdf_file))
        self.pdf_viewer.setDocument(self.pdf_doc)
        self.tabWidget.setCurrentIndex(1)

    def add_menu_entry(self) -> None:
        completed_process = install_desktop_shortcut()
        if completed_process.returncode == 0:
            QMessageBox.information(
                self, "Shortcut installed", "This application was successfully added to start menu."
            )
        else:
            QMessageBox.critical(self, "Unable to install shortcut", completed_process.stdout)

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
                path, _ = QFileDialog.getOpenFileName(
                    self,
                    "Open MCQ file",
                    str(self.settings.current_dir),
                    ";;".join(FILES_FILTER),
                    FILES_FILTER[0],
                )
            if path:
                self.settings.current_file = path  # type: ignore
                self.current_file_saved = True
                with open(path, encoding="utf8") as f:
                    self.mcq_editor.setText(f.read())
                self.mark_as_saved()
            else:
                print("open_file action canceled.")
        else:
            print("open_file action canceled.")

    def save_file_as(self, *, path: str | Path | None = None) -> None:
        if path is None:
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
        # Tell Scintilla that the current editor's state is its new saved state.
        # More information on Scintilla messages: http://www.scintilla.org/ScintillaDoc.html
        self.mcq_editor.SendScintilla(QsciScintilla.SCI_SETSAVEPOINT)

    def _on_text_changed(self) -> None:
        self.current_file_saved = False
        self.update_title()

    def _on_text_saved(self) -> None:
        self.current_file_saved = True
        self.update_title()

    def get_current_file_name(self):
        return self.settings.current_file.name if self.settings.current_file.is_file() else ""

    def update_title(self) -> None:
        self.setWindowTitle(
            f"MCQ Editor - {self.get_current_file_name()}" + ("" if self.current_file_saved else " *")
        )

    def dbg_send_scintilla_command(self) -> None:
        dialog = QDialog(self)
        ui = dbg_send_scintilla_messages_ui.Ui_Dialog()
        ui.setupUi(dialog)

        def send_command_and_display_return() -> None:
            editor = self.mcq_editor
            message_name = "SCI_" + ui.message_name.text()
            msg = getattr(editor, message_name, None)
            args = [eval(arg) for arg in ui.message_args.text().split(",") if arg.strip()]
            if msg is None:
                ui.return_label.setText(f"Invalid message name: {message_name}.")
            else:
                try:
                    val = editor.SendScintilla(msg, *args)
                    ui.return_label.setText(f"Return: {val!r}")
                except Exception as e:
                    ui.return_label.setText(f"Return: {e!r}")

        ui.sendButton.pressed.connect(send_command_and_display_return)
        dialog.show()
