from PyQt6.QtWidgets import QTabWidget, QDockWidget, QWidget
from ptyx.compilation import compile_latex_to_pdf
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
        dock = self.parent().parent()
        assert isinstance(dock, QDockWidget)
        return dock

    def generate_pdf(self) -> None:
        self.dock.show()
        self.latex_viewer.generate_latex()
        self.pdf_viewer.generate_pdf()
        self.setCurrentIndex(self.indexOf(self.pdf_viewer))

    def generate_latex(self) -> None:
        self.dock.show()
        self.latex_viewer.generate_latex()
        self.setCurrentIndex(self.indexOf(self.latex_viewer))

    def update_tabs(self) -> None:
        self.latex_viewer.load()
        self.pdf_viewer.load()
