#!/usr/bin/python3
import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory, mkdtemp

import PyQt6.QtPdfWidgets
import ptyx_mcq
from PyQt6 import Qsci, QtPdfWidgets
from PyQt6.Qsci import QsciScintilla
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtPdf import QPdfDocument
from PyQt6.QtWidgets import QMainWindow, QApplication
from ptyx.latex_generator import compiler
from ptyx.compilation import compile_latex, _build_command

from ptyx_mcq_editor.lexer import MyLexer
from ptyx_mcq_editor.main import Ui_MainWindow

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


class CustomUiMainWindow(Ui_MainWindow):
    # def __init__(self):
    #     super(CustomMainWindow, self).__init__()

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

    def setupUi(self, window: QMainWindow):
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
        font.setPointSize(14)
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

        self.pdf_viewer = QtPdfWidgets.QPdfView(self.pdf_tab)
        self.pdf_viewer.setObjectName("pdf_viewer")
        self.pdf_tab_grid.addWidget(self.pdf_viewer, 0, 0, 1, 1)

        self.tmp_dir = Path(mkdtemp(prefix="mcq-editor-"))
        print("created temporary directory", self.tmp_dir)
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

    def display_latex(self):
        self.latex_editor.setText(self._get_latex())
        self.tabWidget.setCurrentIndex(0)

    def display_pdf(self):
        (latex_file := self.tmp_dir / "tmp.tex").write_text(self._get_latex())
        pdf_file = self.tmp_dir / "tmp.pdf"
        print(_build_command(latex_file, pdf_file))
        compile_latex(latex_file, dest=self.tmp_dir)
        self.pdf_doc = QPdfDocument(self.pdf_viewer)
        self.pdf_doc.load(str(pdf_file))
        self.pdf_viewer.setDocument(self.pdf_doc)

    def __del__(self):
        shutil.rmtree(self.tmp_dir)


def main():
    import sys

    app = QApplication(sys.argv)
    main_window = QMainWindow()
    ui = CustomUiMainWindow()
    ui.setupUi(main_window)
    (ui.action_LaTeX.triggered.connect(ui.display_latex))
    (ui.action_Pdf.triggered.connect(ui.display_pdf))
    main_window.show()
    sys.exit(app.exec())
    # app = QApplication(sys.argv)
    # QApplication.setStyle(QStyleFactory.create("Fusion"))
    # # noinspection PyUnusedLocal
    # gui = CustomMainWindow()  # noqa: F841
    #
    # sys.exit(app.exec())


if __name__ == "__main__":
    main()
