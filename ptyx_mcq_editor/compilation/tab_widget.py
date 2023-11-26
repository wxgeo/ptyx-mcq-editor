from PyQt6.QtWidgets import QTabWidget, QDockWidget
from ptyx.compilation import compile_latex_to_pdf
from ptyx_mcq_editor.enhanced_widget import EnhancedWidget

from ptyx_mcq_editor.compilation.pdf_viewer import PdfViewer

from ptyx_mcq_editor.compilation.latex_viewer import LatexViewer


class CompilationTabs(QTabWidget, EnhancedWidget):
    def __init__(self, parent: QDockWidget):
        super().__init__(parent=parent)
        self.latex_viewer = LatexViewer(self)
        self.pdf_viewer = PdfViewer(self)
        self.addTab(self.latex_viewer, "LaTeX Code")
        self.addTab(self.pdf_viewer, "Pdf Rendering")

    def display_pdf(self) -> None:
        main_window = self.get_main_window()
        latex = self.latex_viewer.load()
        (latex_file := main_window.tmp_dir / "tmp.tex").write_text(latex)
        pdf_file = main_window.tmp_dir / "tmp.pdf"
        # print(_build_command(latex_file, pdf_file))
        compilation_info = compile_latex_to_pdf(latex_file, dest=main_window.tmp_dir)
        self.pdf_viewer.load(pdf_file)
        self.setCurrentIndex(self.indexOf(self.pdf_viewer))

    def display_latex(self) -> None:
        self.latex_viewer.load()
        self.setCurrentIndex(self.indexOf(self.latex_viewer))
