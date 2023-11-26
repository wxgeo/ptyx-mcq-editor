from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6 import QtPdfWidgets
from PyQt6.QtPdf import QPdfDocument
from ptyx.compilation import compile_latex_to_pdf

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

if TYPE_CHECKING:
    from ptyx_mcq_editor.main_window import McqEditorMainWindow


class PdfViewer(QtPdfWidgets.QPdfView, EnhancedWidget):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.pdf_viewer = QtPdfWidgets.QPdfView(None)
        self.doc = QPdfDocument(self)
        self.setDocument(self.doc)

    def load(self, pdf_path: Path) -> None:
        self.doc.load(str(pdf_path))
