from pathlib import Path

from PyQt6.QtWidgets import QTabWidget, QDockWidget, QWidget
from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

from ptyx_mcq_editor.compilation.pdf_viewer import PdfViewer

from ptyx_mcq_editor.compilation.latex_viewer import LatexViewer


class CompilationTabs(QTabWidget, EnhancedWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent=parent)
        self.latex_viewer = LatexViewer(self)
        self.pdf_viewer = PdfViewer(self)
        self.addTab(self.latex_viewer, "LaTeX Code")
        self.addTab(self.pdf_viewer, "Pdf Rendering")

    @property
    def dock(self) -> QDockWidget:
        dock = self.parent().parent()  # type: ignore
        assert isinstance(dock, QDockWidget)
        return dock

    def generate_pdf(self, doc_path: Path = None) -> None:
        self.dock.show()
        self.latex_viewer.generate_latex(doc_path=doc_path)
        self.pdf_viewer.generate_pdf(doc_path=doc_path)
        self.setCurrentIndex(self.indexOf(self.pdf_viewer))

    def generate_latex(self, doc_path: Path = None) -> None:
        self.dock.show()
        self.latex_viewer.generate_latex(doc_path=doc_path)
        self.setCurrentIndex(self.indexOf(self.latex_viewer))

    def update_tabs(self) -> None:
        self.latex_viewer.load()
        self.pdf_viewer.load()
