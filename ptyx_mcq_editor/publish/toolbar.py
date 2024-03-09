from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import QToolBar, QSpinBox, QLabel

from ptyx_mcq_editor.enhanced_widget import EnhancedWidget


# class PublishDock(QDockWidget, EnhancedWidget):
#     ...


# class PublishWidget(EnhancedWidget, Ui_publish_widget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setupUi(self)


class PublishToolBar(QToolBar, EnhancedWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.addWidget(QLabel("Number of documents: ", self))
        self.spinbox = QSpinBox(self)
        self.spinbox.setAccelerated(True)
        self.spinbox.setMinimum(1)
        self.spinbox.setMaximum(1000)
        self.addWidget(self.spinbox)
        self.spinbox.setStyleSheet("margin-right:10px")
        self.action_generate = QAction("Generate", self)
        font = QFont()
        font.setWeight(QFont.Weight.Bold)
        self.action_generate.setFont(font)
        self.addAction(self.action_generate)
        # self.generate_docs_button = QToolButton(self)
        # self.generate_docs_button.setText("Generate")
        # self.generate_docs_button.setStyleSheet("font-weight: bold;\n" "margin-left: 10px;")
        # self.addWidget(self.generate_docs_button)
        self.action_generate.triggered.connect(self.publish)

    def publish(self):
        print("Hello !")
