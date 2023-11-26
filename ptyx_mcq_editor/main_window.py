#!/usr/bin/python3
import shutil
from functools import partial
from pathlib import Path
from tempfile import mkdtemp

from PyQt6.QtGui import QCloseEvent, QIcon
from PyQt6.QtWidgets import QMainWindow, QMessageBox

from ptyx_mcq_editor.file_events_handler import FileEventsHandler

from ptyx_mcq_editor.editor.editor_tab import EditorTab

from ptyx_mcq_editor.editor.editor_widget import EditorWidget
from ptyx_mcq_editor.settings import Settings, Side, Document
from ptyx_mcq_editor.tools import install_desktop_shortcut
from ptyx_mcq_editor.generated_ui.main_ui import Ui_MainWindow

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


ICON_PATH = Path(__file__).parent.parent / "ressources/mcq-editor.svg"


class McqEditorMainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        super().__init__(parent=None)
        self.settings = Settings.load_settings()
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

        # -----------------
        # Customize display
        # -----------------
        if not ICON_PATH.is_file():
            print(f"File not found: {ICON_PATH}")
        else:
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.search_dock.setVisible(False)
        self.search_dock.main_window = self

        self.update_ui()

        # TODO: enable right view
        self.hide_right_view()

        # -------------------
        #   Connect signals
        # -------------------
        self.connect_menu_signals()
        self.search_dock.connect_signals()

        self.restore_previous_session()

    def connect_menu_signals(self) -> None:
        self.action_New.triggered.connect(partial(self.file_events_handler.new_doc, side=None))
        self.action_Open.triggered.connect(partial(self.file_events_handler.open_doc, side=None))
        self.action_Save.triggered.connect(partial(self.file_events_handler.save_doc, side=None, index=None))
        self.action_Close.triggered.connect(
            partial(self.file_events_handler.close_doc, side=None, index=None)
        )
        self.actionSave_as.triggered.connect(
            partial(self.file_events_handler.save_doc_as, side=None, index=None)
        )
        self.action_LaTeX.triggered.connect(self.compilation_tabs.display_latex)
        self.action_Pdf.triggered.connect(self.compilation_tabs.display_pdf)
        self.action_Add_MCQ_Editor_to_start_menu.triggered.connect(self.add_desktop_menu_entry)
        self.actionFind.triggered.connect(
            partial(self.search_dock.toggle_find_and_replace_dialog, replace=False)
        )
        self.actionReplace.triggered.connect(
            partial(self.search_dock.toggle_find_and_replace_dialog, replace=True)
        )
        self.menuFichier.aboutToShow.connect(self.update_recent_files_menu)
        self.action_Send_Qscintilla_Command.triggered.connect(self.dbg_send_scintilla_command)

    def restore_previous_session(self) -> None:
        for side, book in self.books.items():
            paths = [doc.path for doc in self.settings.docs(side) if doc.path is not None]
            if paths:
                self.file_events_handler.open_doc(side=side, paths=paths)
        if all(len(self.settings.docs(side)) == 0 for side in Side):
            self.file_events_handler.new_doc(Side.LEFT)

    # noinspection PyMethodOverriding
    def closeEvent(self, event: QCloseEvent | None) -> None:
        assert event is not None
        assert self is not None
        if self.request_to_close():
            event.accept()
        else:
            event.ignore()

    @property
    def current_mcq_editor(self) -> EditorWidget:
        side = self.settings.current_side
        current_book = self.books[side]
        current_tab = current_book.currentWidget()
        assert isinstance(current_tab, EditorTab), current_tab
        return current_tab.editor

    def hide_right_view(self) -> None:
        self.right_tab_widget.hide()

    def request_to_close(self) -> bool:
        if self.file_events_handler.ask_for_saving_if_needed():
            self.settings.save_settings()
            shutil.rmtree(self.tmp_dir)
            return True
        return False

    def update_recent_files_menu(self) -> None:
        recent_files = tuple(self.settings.recent_files)
        if not recent_files:
            self.menu_Recent_Files.menuAction().setVisible(False)
        else:
            self.menu_Recent_Files.clear()
            for recent_file in recent_files:
                action = self.menu_Recent_Files.addAction(recent_file.name)
                action.triggered.connect(partial(self.file_events_handler.open_doc, paths=[recent_file]))
            self.menu_Recent_Files.menuAction().setVisible(True)

    # def _get_latex(self) -> str:
    #     template = (Path(ptyx_mcq.__file__).parent / "templates/original/new.ptyx").read_text()
    #     content = self.current_mcq_editor.text()
    #     if not content.lstrip().startswith("* "):
    #         content = "* \n" + content
    #     # re.sub() doesn't seem to work when "\dfrac" is in the replacement string... using re.split() instead.
    #     before, _, after = re.split("(<<<.+>>>)", template, flags=re.MULTILINE | re.DOTALL)
    #     ptyx_code = f"{before}\n<<<\n{content}\n>>>\n{after}"
    #     compiler = Compiler()
    #     latex = compiler.parse(
    #         code=ptyx_code, MCQ_KEEP_ALL_VERSIONS=True, PTYX_WITH_ANSWERS=True, MCQ_REMOVE_HEADER=True
    #     )
    #     return latex

    # def display_latex(self) -> None:
    #     self.latex_editor.setText(self._get_latex())
    #     self.tabWidget.setCurrentIndex(0)

    # def display_pdf(self) -> None:
    #     self.latex_editor.setText(latex := self._get_latex())
    #     (latex_file := self.tmp_dir / "tmp.tex").write_text(latex)
    #     pdf_file = self.tmp_dir / "tmp.pdf"
    #     # print(_build_command(latex_file, pdf_file))
    #     compilation_info = compile_latex_to_pdf(latex_file, dest=self.tmp_dir)
    #     self.pdf_doc.setParent(self.pdf_viewer)
    #     self.pdf_doc.load(str(pdf_file))
    #     self.pdf_viewer.setDocument(self.pdf_doc)
    #     self.tabWidget.setCurrentIndex(1)

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

    def update_ui(self) -> None:
        # Update window and tab titles
        doc: Document | None = self.settings.docs().current_doc
        window_title = "MCQ Editor"
        if doc is not None:
            window_title = f"{window_title} - {doc.title}"
            current_side = self.settings.current_side
            book = self.books[current_side]
            book.setTabText(self.settings.docs().current_index, doc.title)
            book.currentWidget().editor.setFocus()
        self.setWindowTitle(window_title)

        # Verify integrity
        for side, book in self.books.items():
            docs = self.settings.docs(side)
            assert (len_ui := book.count()) == (len_settings := len(docs)), (len_ui, len_settings)
            assert (ui_index := book.currentIndex()) == (settings_index := docs.current_index) or (
                ui_index == -1 and settings_index is None
            ), (ui_index, settings_index)
            for i, doc in enumerate(docs):
                assert book.widget(i).doc is doc
                assert book.tabText(i) == doc.title

    def dbg_send_scintilla_command(self):
        self.current_mcq_editor.dbg_send_scintilla_command()
