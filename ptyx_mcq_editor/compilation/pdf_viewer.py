from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6 import QtPdfWidgets
from PyQt6.QtPdf import QPdfDocument
from ptyx.compilation import compile_latex_to_pdf

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

if TYPE_CHECKING:
    pass


class PdfViewer(QtPdfWidgets.QPdfView, EnhancedWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        # self.pdf_viewer = QtPdfWidgets.QPdfView(None)
        self.setPageMode(QtPdfWidgets.QPdfView.PageMode.MultiPage)
        self.doc = QPdfDocument(self)
        self.setDocument(self.doc)

    def _latex_file_path(self) -> Path | None:
        """Get the path of the current latex file."""
        return self.main_window.get_temp_path("pdf")

    def generate_pdf(self) -> None:
        latex_file = self.main_window.get_temp_path("tex")
        assert latex_file is not None
        compilation_info = compile_latex_to_pdf(latex_file, dest=self.main_window.tmp_dir)
        print(compilation_info)
        self.load()

    def load(self) -> None:
        pdf_path = self._latex_file_path()
        if pdf_path is not None and pdf_path.is_file():
            self.doc.load(str(pdf_path))
            print(self.doc.pageCount())
        else:
            self.doc.load(None)
