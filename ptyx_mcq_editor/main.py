# Form implementation generated from reading ui file 'interfaces/main.ui'
#
# Created by: PyQt6 UI code generator 6.6.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(816, 507)
        MainWindow.setAcceptDrops(False)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.mcq_editor = Qsci.QsciScintilla(parent=self.centralwidget)
        self.mcq_editor.setToolTip("")
        self.mcq_editor.setWhatsThis("")
        self.mcq_editor.setObjectName("mcq_editor")
        self.gridLayout.addWidget(self.mcq_editor, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 816, 23))
        self.menubar.setObjectName("menubar")
        self.menuFichier = QtWidgets.QMenu(parent=self.menubar)
        self.menuFichier.setObjectName("menuFichier")
        self.menuCompilation = QtWidgets.QMenu(parent=self.menubar)
        self.menuCompilation.setObjectName("menuCompilation")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.dockWidget = QtWidgets.QDockWidget(parent=MainWindow)
        self.dockWidget.setEnabled(True)
        self.dockWidget.setFloating(False)
        self.dockWidget.setObjectName("dockWidget")
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.dockWidgetContents)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.latex_browser = QtWidgets.QTextBrowser(parent=self.dockWidgetContents)
        self.latex_browser.setEnabled(True)
        self.latex_browser.setObjectName("latex_browser")
        self.gridLayout_2.addWidget(self.latex_browser, 0, 0, 1, 1)
        self.dockWidget.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.dockWidget)
        self.actionNouveau = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("document-new")
        self.actionNouveau.setIcon(icon)
        self.actionNouveau.setObjectName("actionNouveau")
        self.action_Open = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("document-open")
        self.action_Open.setIcon(icon)
        self.action_Open.setObjectName("action_Open")
        self.action_Save = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("document-save")
        self.action_Save.setIcon(icon)
        self.action_Save.setObjectName("action_Save")
        self.actionSave_as = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("document-save-as")
        self.actionSave_as.setIcon(icon)
        self.actionSave_as.setObjectName("actionSave_as")
        self.action_Quitter = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("application-exit")
        self.action_Quitter.setIcon(icon)
        self.action_Quitter.setObjectName("action_Quitter")
        self.action_LaTeX = QtGui.QAction(parent=MainWindow)
        self.action_LaTeX.setObjectName("action_LaTeX")
        self.action_Pdf = QtGui.QAction(parent=MainWindow)
        self.action_Pdf.setObjectName("action_Pdf")
        self.menuFichier.addAction(self.actionNouveau)
        self.menuFichier.addAction(self.action_Open)
        self.menuFichier.addAction(self.action_Save)
        self.menuFichier.addAction(self.actionSave_as)
        self.menuFichier.addSeparator()
        self.menuFichier.addAction(self.action_Quitter)
        self.menuCompilation.addAction(self.action_LaTeX)
        self.menuCompilation.addAction(self.action_Pdf)
        self.menubar.addAction(self.menuFichier.menuAction())
        self.menubar.addAction(self.menuCompilation.menuAction())

        self.retranslateUi(MainWindow)
        self.action_Quitter.triggered.connect(MainWindow.close) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MCQ Editor"))
        self.menuFichier.setTitle(_translate("MainWindow", "&File"))
        self.menuCompilation.setTitle(_translate("MainWindow", "&Compilation"))
        self.dockWidget.setWindowTitle(_translate("MainWindow", "LaTeX code"))
        self.actionNouveau.setText(_translate("MainWindow", "&New"))
        self.actionNouveau.setShortcut(_translate("MainWindow", "Ctrl+N"))
        self.action_Open.setText(_translate("MainWindow", "&Open"))
        self.action_Open.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.action_Save.setText(_translate("MainWindow", "&Save"))
        self.action_Save.setShortcut(_translate("MainWindow", "Ctrl+S"))
        self.actionSave_as.setText(_translate("MainWindow", "Save &as"))
        self.actionSave_as.setShortcut(_translate("MainWindow", "Ctrl+Shift+S"))
        self.action_Quitter.setText(_translate("MainWindow", "&Quitter"))
        self.action_Quitter.setShortcut(_translate("MainWindow", "Ctrl+Q"))
        self.action_LaTeX.setText(_translate("MainWindow", "&LaTeX"))
        self.action_LaTeX.setShortcut(_translate("MainWindow", "Ctrl+L"))
        self.action_Pdf.setText(_translate("MainWindow", "&Pdf"))
        self.action_Pdf.setShortcut(_translate("MainWindow", "Ctrl+P"))
from PyQt6 import Qsci


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
