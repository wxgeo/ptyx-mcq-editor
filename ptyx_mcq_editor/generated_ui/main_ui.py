# Form implementation generated from reading ui file 'ui/main.ui'
#
# Created by: PyQt6 UI code generator 6.6.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1142, 862)
        MainWindow.setAcceptDrops(False)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.splitter = QtWidgets.QSplitter(parent=self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.splitter.setObjectName("splitter")
        self.left_tab_widget = FilesBook(parent=self.splitter)
        self.left_tab_widget.setObjectName("left_tab_widget")
        self.right_tab_widget = FilesBook(parent=self.splitter)
        self.right_tab_widget.setObjectName("right_tab_widget")
        self.verticalLayout.addWidget(self.splitter)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1142, 23))
        self.menubar.setObjectName("menubar")
        self.menuFichier = QtWidgets.QMenu(parent=self.menubar)
        self.menuFichier.setObjectName("menuFichier")
        self.menu_Recent_Files = QtWidgets.QMenu(parent=self.menuFichier)
        self.menu_Recent_Files.setObjectName("menu_Recent_Files")
        self.menuCompilation = QtWidgets.QMenu(parent=self.menubar)
        self.menuCompilation.setObjectName("menuCompilation")
        self.menu_Tools = QtWidgets.QMenu(parent=self.menubar)
        self.menu_Tools.setObjectName("menu_Tools")
        self.menu_Edit = QtWidgets.QMenu(parent=self.menubar)
        self.menu_Edit.setObjectName("menu_Edit")
        self.menu_propos = QtWidgets.QMenu(parent=self.menubar)
        self.menu_propos.setObjectName("menu_propos")
        self.menuDebug = QtWidgets.QMenu(parent=self.menubar)
        self.menuDebug.setObjectName("menuDebug")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.compilation_dock = QtWidgets.QDockWidget(parent=MainWindow)
        self.compilation_dock.setEnabled(True)
        self.compilation_dock.setFloating(False)
        self.compilation_dock.setObjectName("compilation_dock")
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.compilation_tabs = CompilationTabs(parent=self.dockWidgetContents)
        self.compilation_tabs.setObjectName("compilation_tabs")
        self.verticalLayout_3.addWidget(self.compilation_tabs)
        self.compilation_dock.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(8), self.compilation_dock)
        self.search_dock = FindAndReplaceWidget(parent=MainWindow)
        self.search_dock.setObjectName("search_dock")
        self.dockWidgetContents_2 = QtWidgets.QWidget()
        self.dockWidgetContents_2.setObjectName("dockWidgetContents_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.dockWidgetContents_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.texts_fields = QtWidgets.QFormLayout()
        self.texts_fields.setObjectName("texts_fields")
        self.findLabel = QtWidgets.QLabel(parent=self.dockWidgetContents_2)
        self.findLabel.setObjectName("findLabel")
        self.texts_fields.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.findLabel)
        self.find_field = QtWidgets.QLineEdit(parent=self.dockWidgetContents_2)
        self.find_field.setObjectName("find_field")
        self.texts_fields.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.find_field)
        self.replace_label = QtWidgets.QLabel(parent=self.dockWidgetContents_2)
        self.replace_label.setObjectName("replace_label")
        self.texts_fields.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.replace_label)
        self.replace_field = QtWidgets.QLineEdit(parent=self.dockWidgetContents_2)
        self.replace_field.setObjectName("replace_field")
        self.texts_fields.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.replace_field)
        self.verticalLayout_2.addLayout(self.texts_fields)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.options = QtWidgets.QGroupBox(parent=self.dockWidgetContents_2)
        self.options.setObjectName("options")
        self.gridLayout = QtWidgets.QGridLayout(self.options)
        self.gridLayout.setObjectName("gridLayout")
        self.caseCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.caseCheckBox.setChecked(True)
        self.caseCheckBox.setObjectName("caseCheckBox")
        self.gridLayout.addWidget(self.caseCheckBox, 0, 0, 1, 1)
        self.selectionOnlyCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.selectionOnlyCheckBox.setObjectName("selectionOnlyCheckBox")
        self.gridLayout.addWidget(self.selectionOnlyCheckBox, 3, 0, 1, 1)
        self.wholeCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.wholeCheckBox.setObjectName("wholeCheckBox")
        self.gridLayout.addWidget(self.wholeCheckBox, 0, 1, 1, 1)
        self.regexCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.regexCheckBox.setObjectName("regexCheckBox")
        self.gridLayout.addWidget(self.regexCheckBox, 3, 1, 1, 1)
        self.horizontalLayout.addWidget(self.options)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.buttons_field = QtWidgets.QHBoxLayout()
        self.buttons_field.setObjectName("buttons_field")
        self.replace_all_button = QtWidgets.QPushButton(parent=self.dockWidgetContents_2)
        self.replace_all_button.setObjectName("replace_all_button")
        self.buttons_field.addWidget(self.replace_all_button)
        self.replace_button = QtWidgets.QPushButton(parent=self.dockWidgetContents_2)
        self.replace_button.setAutoDefault(True)
        self.replace_button.setObjectName("replace_button")
        self.buttons_field.addWidget(self.replace_button)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.buttons_field.addItem(spacerItem1)
        self.previous_button = QtWidgets.QPushButton(parent=self.dockWidgetContents_2)
        self.previous_button.setCheckable(False)
        self.previous_button.setAutoDefault(True)
        self.previous_button.setObjectName("previous_button")
        self.buttons_field.addWidget(self.previous_button)
        self.next_button = QtWidgets.QPushButton(parent=self.dockWidgetContents_2)
        self.next_button.setAutoDefault(True)
        self.next_button.setDefault(False)
        self.next_button.setObjectName("next_button")
        self.buttons_field.addWidget(self.next_button)
        self.verticalLayout_2.addLayout(self.buttons_field)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_2.addItem(spacerItem2)
        self.search_dock.setWidget(self.dockWidgetContents_2)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.search_dock)
        self.action_New = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("document-new")
        self.action_New.setIcon(icon)
        self.action_New.setObjectName("action_New")
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
        self.action_Add_MCQ_Editor_to_start_menu = QtGui.QAction(parent=MainWindow)
        self.action_Add_MCQ_Editor_to_start_menu.setObjectName("action_Add_MCQ_Editor_to_start_menu")
        self.actionFind = QtGui.QAction(parent=MainWindow)
        self.actionFind.setObjectName("actionFind")
        self.actionReplace = QtGui.QAction(parent=MainWindow)
        self.actionReplace.setObjectName("actionReplace")
        self.actionNone = QtGui.QAction(parent=MainWindow)
        self.actionNone.setObjectName("actionNone")
        self.action_Send_Qscintilla_Command = QtGui.QAction(parent=MainWindow)
        self.action_Send_Qscintilla_Command.setObjectName("action_Send_Qscintilla_Command")
        self.action_Close = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("window-close")
        self.action_Close.setIcon(icon)
        self.action_Close.setObjectName("action_Close")
        self.menu_Recent_Files.addAction(self.actionNone)
        self.menuFichier.addAction(self.action_New)
        self.menuFichier.addAction(self.menu_Recent_Files.menuAction())
        self.menuFichier.addAction(self.action_Open)
        self.menuFichier.addAction(self.action_Save)
        self.menuFichier.addAction(self.actionSave_as)
        self.menuFichier.addAction(self.action_Close)
        self.menuFichier.addSeparator()
        self.menuFichier.addAction(self.action_Quitter)
        self.menuCompilation.addAction(self.action_LaTeX)
        self.menuCompilation.addAction(self.action_Pdf)
        self.menu_Tools.addAction(self.action_Add_MCQ_Editor_to_start_menu)
        self.menu_Edit.addAction(self.actionFind)
        self.menu_Edit.addAction(self.actionReplace)
        self.menuDebug.addAction(self.action_Send_Qscintilla_Command)
        self.menubar.addAction(self.menuFichier.menuAction())
        self.menubar.addAction(self.menuCompilation.menuAction())
        self.menubar.addAction(self.menu_Tools.menuAction())
        self.menubar.addAction(self.menu_Edit.menuAction())
        self.menubar.addAction(self.menuDebug.menuAction())
        self.menubar.addAction(self.menu_propos.menuAction())
        self.findLabel.setBuddy(self.find_field)
        self.replace_label.setBuddy(self.replace_field)

        self.retranslateUi(MainWindow)
        self.left_tab_widget.setCurrentIndex(-1)
        self.right_tab_widget.setCurrentIndex(-1)
        self.compilation_tabs.setCurrentIndex(-1)
        self.action_Quitter.triggered.connect(MainWindow.close) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MCQ Editor"))
        self.menuFichier.setTitle(_translate("MainWindow", "&File"))
        self.menu_Recent_Files.setTitle(_translate("MainWindow", "&Recent Files"))
        self.menuCompilation.setTitle(_translate("MainWindow", "&Make"))
        self.menu_Tools.setTitle(_translate("MainWindow", "&Tools"))
        self.menu_Edit.setTitle(_translate("MainWindow", "&Edit"))
        self.menu_propos.setTitle(_translate("MainWindow", "&About"))
        self.menuDebug.setTitle(_translate("MainWindow", "&Debug"))
        self.compilation_dock.setWindowTitle(_translate("MainWindow", "Output"))
        self.search_dock.setWindowTitle(_translate("MainWindow", "Find and replace"))
        self.findLabel.setText(_translate("MainWindow", "Fi&nd"))
        self.replace_label.setText(_translate("MainWindow", "Re&place with"))
        self.options.setTitle(_translate("MainWindow", "&Options"))
        self.caseCheckBox.setText(_translate("MainWindow", "&Case sensitive"))
        self.selectionOnlyCheckBox.setText(_translate("MainWindow", "&Selection only"))
        self.wholeCheckBox.setText(_translate("MainWindow", "&Whole words only"))
        self.regexCheckBox.setToolTip(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Sans\'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">whether the text to search should be interpreted as a regular expression.</p>\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"></p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\">You may want to take a look at the syntax of regular expressions:</p>\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><a href=\"http://doc.trolltech.com/qregexp.html\"><span style=\" text-decoration: underline; color:#0000ff;\">http://doc.trolltech.com/qregexp.html</span></a></p></body></html>"))
        self.regexCheckBox.setText(_translate("MainWindow", "R&egular Expression"))
        self.replace_all_button.setText(_translate("MainWindow", "Replace &All"))
        self.replace_button.setText(_translate("MainWindow", "&Replace"))
        self.previous_button.setText(_translate("MainWindow", "Pre&vious"))
        self.previous_button.setShortcut(_translate("MainWindow", "Shift+F3"))
        self.next_button.setToolTip(_translate("MainWindow", "Find next occurence (F3)"))
        self.next_button.setText(_translate("MainWindow", "&Next"))
        self.next_button.setShortcut(_translate("MainWindow", "F3"))
        self.action_New.setText(_translate("MainWindow", "&New"))
        self.action_New.setShortcut(_translate("MainWindow", "Ctrl+N"))
        self.action_Open.setText(_translate("MainWindow", "&Open"))
        self.action_Open.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.action_Save.setText(_translate("MainWindow", "&Save"))
        self.action_Save.setShortcut(_translate("MainWindow", "Ctrl+S"))
        self.actionSave_as.setText(_translate("MainWindow", "Save &as"))
        self.actionSave_as.setShortcut(_translate("MainWindow", "Ctrl+Shift+S"))
        self.action_Quitter.setText(_translate("MainWindow", "&Quitter"))
        self.action_LaTeX.setText(_translate("MainWindow", "&LaTeX"))
        self.action_LaTeX.setShortcut(_translate("MainWindow", "Ctrl+Shift+Return"))
        self.action_Pdf.setText(_translate("MainWindow", "&Pdf"))
        self.action_Pdf.setShortcut(_translate("MainWindow", "Ctrl+Return"))
        self.action_Add_MCQ_Editor_to_start_menu.setText(_translate("MainWindow", "&Add shortcut to MCQ Editor in the applications menu"))
        self.actionFind.setText(_translate("MainWindow", "&Find"))
        self.actionFind.setShortcut(_translate("MainWindow", "Ctrl+F"))
        self.actionReplace.setText(_translate("MainWindow", "&Replace"))
        self.actionReplace.setShortcut(_translate("MainWindow", "Ctrl+H"))
        self.actionNone.setText(_translate("MainWindow", "EMPTY"))
        self.action_Send_Qscintilla_Command.setText(_translate("MainWindow", "&Send Qscintilla Command"))
        self.action_Close.setText(_translate("MainWindow", "&Close"))
from ptyx_mcq_editor.compilation.tab_widget import CompilationTabs
from ptyx_mcq_editor.files_book import FilesBook
from ptyx_mcq_editor.find_and_replace import FindAndReplaceWidget


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())