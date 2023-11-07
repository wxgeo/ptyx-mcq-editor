#!/usr/bin/python3
import sys
import re
import shutil
from functools import partial
from pathlib import Path
from tempfile import mkdtemp
from types import TracebackType
from typing import Optional, Type

import ptyx_mcq
from PyQt6 import Qsci, QtPdfWidgets
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QFont, QColor, QDragEnterEvent, QDropEvent
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox
from ptyx.compilation import compile_latex  # , _build_command
from ptyx.latex_generator import compiler

from ptyx_mcq_editor.lexer import MyLexer
from ptyx_mcq_editor.ui.main import Ui_MainWindow

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

FILES_FILTER = ("Mcq Exercises Files (*.ex)", "All Files (*.*)")


class McqEditorMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.ui: Optional[MainWindowContent] = None

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
                assert self.ui is not None
                self.ui.open_file(path=url.toLocalFile())


class MainWindowContent(Ui_MainWindow):
    def __init__(self, window: McqEditorMainWindow) -> None:
        super().__init__()
        self.current_file_saved = True
        self.current_file: Optional[Path] = None
        self.tmp_dir = Path(mkdtemp(prefix="mcq-editor-"))
        self.window = window
        self.pdf_viewer = QtPdfWidgets.QPdfView(None)
        self.pdf_doc = QPdfDocument(None)

        # def __init__(self):

    #     super(McqEditorMainWindow, self).__init__()

    # -------------------------------- #
    #           Window setup           #
    # -------------------------------- #

    # 1. Define the geometry of the main window
    # ------------------------------------------
    # self.setGeometry(200, 200, 900, 500)
    # self.setWindowTitle("QScintilla Test")

    # 2. Create frame and layout
    # ---------------------------
    # self.__frm = QFrame(self)
    # self.__frm.setStyleSheet("QWidget { background-color: #ffeaeaea }")
    # self.__lyt = QVBoxLayout()
    # self.__frm.setLayout(self.__lyt)
    # self.setCentralWidget(self.__frm)

    def setupUi(self, window: McqEditorMainWindow) -> None:
        super().setupUi(window)
        # 3. Place a button
        # ------------------
        # self.__btn = QPushButton("Compile")
        # self.__btn.setFixedWidth(50)
        # self.__btn.setFixedHeight(50)
        # self.__btn.clicked.connect(self.__btn_action)
        # self.__btn.setFont(self.__myFont)
        # self.__lyt.addWidget(self.__btn)

        # -------------------------------- #
        #     QScintilla editor setup      #
        # -------------------------------- #

        # ! Make instance of QSciScintilla class!
        # ----------------------------------------
        # self.mcq_editor = QsciScintilla()
        self.mcq_editor.setText(TEST)  # 'myCodeSample' is a string containing some C-code
        self.mcq_editor.setLexer(None)  # We install lexer later
        self.mcq_editor.setUtf8(True)  # Set encoding to UTF-8
        font = QFont()
        font.setPointSize(13)
        self.mcq_editor.setFont(font)  # Gets overridden by lexer later on

        # 1. Text wrapping
        # -----------------
        self.mcq_editor.setWrapMode(QsciScintilla.WrapMode.WrapWord)
        self.mcq_editor.setWrapVisualFlags(QsciScintilla.WrapVisualFlag.WrapFlagByText)
        self.mcq_editor.setWrapIndentMode(QsciScintilla.WrapIndentMode.WrapIndentIndented)

        # 2. End-of-line mode
        # --------------------
        self.mcq_editor.setEolMode(QsciScintilla.EolMode.EolUnix)
        self.mcq_editor.setEolVisibility(False)

        # 3. Indentation
        # ---------------
        self.mcq_editor.setIndentationsUseTabs(False)
        self.mcq_editor.setTabWidth(4)
        self.mcq_editor.setIndentationGuides(True)
        self.mcq_editor.setTabIndents(True)
        self.mcq_editor.setAutoIndent(True)

        # 4. Caret
        # ---------
        self.mcq_editor.setCaretForegroundColor(QColor("#ff0000ff"))
        self.mcq_editor.setCaretLineVisible(True)
        self.mcq_editor.setCaretLineBackgroundColor(QColor("#1f0000ff"))
        self.mcq_editor.setCaretWidth(2)

        # 5. Margins
        # -----------
        # Margin 0 = Line nr margin
        self.mcq_editor.setMarginType(0, QsciScintilla.MarginType.NumberMargin)
        self.mcq_editor.setMarginWidth(0, "0000")
        self.mcq_editor.setMarginsForegroundColor(QColor("#ff888888"))

        # -------------------------------- #
        #          Install lexer           #
        # -------------------------------- #
        self.mcq_editor.setLexer(MyLexer(self.mcq_editor))
        self.latex_editor.setLexer(Qsci.QsciLexerTeX(self.latex_editor))

        self.pdf_viewer.setParent(self.pdf_tab)
        self.pdf_viewer.setObjectName("pdf_viewer")
        self.pdf_tab_grid.addWidget(self.pdf_viewer, 0, 0, 1, 1)

        print("created temporary directory", self.tmp_dir)

        window.ui = self

        self.action_New.triggered.connect(self.new_file)
        self.action_Open.triggered.connect(self.open_file)
        self.action_Save.triggered.connect(self.save_file)
        self.actionSave_as.triggered.connect(self.save_file_as)
        self.action_LaTeX.triggered.connect(self.display_latex)
        self.action_Pdf.triggered.connect(self.display_pdf)

        self.mcq_editor.textChanged.connect(self.text_changed)

        self.mcq_editor.SCN_SAVEPOINTREACHED.connect(self.text_saved)
        self.mcq_editor.SCN_SAVEPOINTLEFT.connect(self.text_changed)

        self.update_title()

        # ! Add editor to layout !
        # -------------------------
        # self.__lyt.addWidget(self.mcq_editor)
        # self.show()

    def _get_latex(self) -> str:
        template = (Path(ptyx_mcq.__file__).parent / "templates/original/new.ptyx").read_text()
        content = self.mcq_editor.text()
        if not content.lstrip().startswith("* "):
            content = "* " + content
        # re.sub() doesn't seem to work when "\dfrac" is in the replacement string... using re.split() instead.
        before, _, after = re.split("(<<<.+>>>)", template, flags=re.MULTILINE | re.DOTALL)
        ptyx_code = f"{before}\n<<<\n{content}\n>>>\n{after}"
        latex = compiler.parse(
            code=ptyx_code, context={"MCQ_KEEP_ALL_VERSIONS": True, "PTYX_WITH_ANSWERS": True}
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
        compile_latex(latex_file, dest=self.tmp_dir)
        self.pdf_doc.setParent(self.pdf_viewer)
        self.pdf_doc.load(str(pdf_file))
        self.pdf_viewer.setDocument(self.pdf_doc)
        self.tabWidget.setCurrentIndex(1)

    def new_file(self) -> None:
        if self.ask_for_saving_if_needed():
            self.mcq_editor.setText("")
            self.current_file = None
            self.mark_as_saved()
        else:
            print("new_file action canceled.")

    def open_file(self, *, path: str | Path | None = None) -> None:
        if self.ask_for_saving_if_needed():
            if path is None:
                directory: Path = Path.cwd() if self.current_file is None else self.current_file.parent
                path, _ = QFileDialog.getOpenFileName(
                    self.window, "Open MCQ file", str(directory), ";;".join(FILES_FILTER), FILES_FILTER[0]
                )
            if path:
                self.current_file = Path(path)
                self.current_file_saved = True
                with open(path, encoding="utf8") as f:
                    self.mcq_editor.setText(f.read())
                self.update_title()
        else:
            print("open_file action canceled.")

    def save_file_as(self, *, path: str | Path | None = None) -> None:
        if path is None:
            path = Path.cwd() if self.current_file is None else self.current_file
            path, _ = QFileDialog.getSaveFileName(
                self.window, "Save as...", str(path), ";;".join(FILES_FILTER), FILES_FILTER[0]
            )
        if path:
            self.current_file = Path(path)
            with open(path, "w", encoding="utf8") as f:
                f.write(self.mcq_editor.text())
            self.mark_as_saved()

    def save_file(self) -> None:
        self.save_file_as(path=self.current_file)

    def ask_for_saving_if_needed(self) -> bool:
        """Ask user what to do if file is not saved.

        Return `False` if user discard operation, else `True`."""
        if self.current_file_saved:
            return True
        dialog = QMessageBox(self.window)
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

    def close(self) -> None:
        if self.ask_for_saving_if_needed():
            self.window.close()

    def mark_as_saved(self) -> None:
        # Tell Scintilla that the current editor's state is its new saved state.
        # More information on Scintilla messages: http://www.scintilla.org/ScintillaDoc.html
        self.mcq_editor.SendScintilla(QsciScintilla.SCI_SETSAVEPOINT)

    def text_changed(self) -> None:
        self.current_file_saved = False
        self.update_title()

    def text_saved(self) -> None:
        self.current_file_saved = True
        self.update_title()

    def _get_current_file_name(self) -> str:
        return self.current_file.name if self.current_file is not None else "<New File>"

    def update_title(self) -> None:
        self.window.setWindowTitle(
            f"MCQ Editor - {self._get_current_file_name()}" + ("" if self.current_file_saved else " *")
        )


def my_excepthook(
    type_: Type[BaseException],
    value: BaseException,
    traceback: TracebackType | None,
    window: QMainWindow = None,
) -> None:
    # log the exception here
    QMessageBox.critical(window, "Something went wrong!", f"{type(value).__name__}: {value}")
    # then call the default handler
    sys.__excepthook__(type_, value, traceback)


def main() -> None:
    # Don't close pyQt application on failure.
    try:
        app = QApplication(sys.argv)
        main_window = McqEditorMainWindow()
        sys.excepthook = partial(my_excepthook, window=main_window)
        ui = MainWindowContent(main_window)
        ui.setupUi(main_window)
        main_window.show()
        return_code = app.exec()
        shutil.rmtree(ui.tmp_dir)
    except BaseException as e:
        raise e

    sys.exit(return_code)


# app = QApplication(sys.argv)
# QApplication.setStyle(QStyleFactory.create("Fusion"))
# # noinspection PyUnusedLocal
# gui = McqEditorMainWindow()  # noqa: F841
#
# sys.exit(app.exec())


if __name__ == "__main__":
    main()
