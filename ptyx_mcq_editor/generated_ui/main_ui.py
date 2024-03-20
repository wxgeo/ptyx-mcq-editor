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
        MainWindow.resize(1509, 862)
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
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1509, 23))
        self.menubar.setObjectName("menubar")
        self.menuFichier = QtWidgets.QMenu(parent=self.menubar)
        self.menuFichier.setObjectName("menuFichier")
        self.menu_Recent_Files = QtWidgets.QMenu(parent=self.menuFichier)
        icon = QtGui.QIcon.fromTheme("document-open-recent")
        self.menu_Recent_Files.setIcon(icon)
        self.menu_Recent_Files.setObjectName("menu_Recent_Files")
        self.menu_New = QtWidgets.QMenu(parent=self.menuFichier)
        icon = QtGui.QIcon.fromTheme("document-new")
        self.menu_New.setIcon(icon)
        self.menu_New.setObjectName("menu_New")
        self.menuCompilation = QtWidgets.QMenu(parent=self.menubar)
        self.menuCompilation.setObjectName("menuCompilation")
        self.menu_Tools = QtWidgets.QMenu(parent=self.menubar)
        self.menu_Tools.setObjectName("menu_Tools")
        self.menu_Edit = QtWidgets.QMenu(parent=self.menubar)
        self.menu_Edit.setObjectName("menu_Edit")
        self.menu_help = QtWidgets.QMenu(parent=self.menubar)
        self.menu_help.setObjectName("menu_help")
        self.menuDebug = QtWidgets.QMenu(parent=self.menubar)
        self.menuDebug.setObjectName("menuDebug")
        self.menu_Code = QtWidgets.QMenu(parent=self.menubar)
        self.menu_Code.setObjectName("menu_Code")
        self.menuImports = QtWidgets.QMenu(parent=self.menu_Code)
        self.menuImports.setObjectName("menuImports")
        self.menuScan = QtWidgets.QMenu(parent=self.menubar)
        self.menuScan.setObjectName("menuScan")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.compilation_dock = QtWidgets.QDockWidget(parent=MainWindow)
        self.compilation_dock.setEnabled(True)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Preferred, QtWidgets.QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.compilation_dock.sizePolicy().hasHeightForWidth())
        self.compilation_dock.setSizePolicy(sizePolicy)
        self.compilation_dock.setMinimumSize(QtCore.QSize(800, 42))
        self.compilation_dock.setFloating(False)
        self.compilation_dock.setObjectName("compilation_dock")
        self.dockWidgetContents = QtWidgets.QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.compilation_tabs = CompilationTabs(parent=self.dockWidgetContents)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.compilation_tabs.sizePolicy().hasHeightForWidth())
        self.compilation_tabs.setSizePolicy(sizePolicy)
        self.compilation_tabs.setObjectName("compilation_tabs")
        self.verticalLayout_3.addWidget(self.compilation_tabs)
        self.compilation_dock.setWidget(self.dockWidgetContents)
        MainWindow.addDockWidget(QtCore.Qt.DockWidgetArea(2), self.compilation_dock)
        self.search_dock = FindAndReplaceWidget(parent=MainWindow)
        self.search_dock.setObjectName("search_dock")
        self.dockWidgetContents_2 = QtWidgets.QWidget()
        self.dockWidgetContents_2.setObjectName("dockWidgetContents_2")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.dockWidgetContents_2)
        self.verticalLayout_2.setContentsMargins(11, 11, 11, 11)
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
        self.selectionOnlyCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.selectionOnlyCheckBox.setObjectName("selectionOnlyCheckBox")
        self.gridLayout.addWidget(self.selectionOnlyCheckBox, 3, 0, 1, 1)
        self.caseCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.caseCheckBox.setChecked(True)
        self.caseCheckBox.setObjectName("caseCheckBox")
        self.gridLayout.addWidget(self.caseCheckBox, 0, 0, 1, 1)
        self.wholeCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.wholeCheckBox.setObjectName("wholeCheckBox")
        self.gridLayout.addWidget(self.wholeCheckBox, 0, 1, 1, 1)
        self.regexCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.regexCheckBox.setObjectName("regexCheckBox")
        self.gridLayout.addWidget(self.regexCheckBox, 3, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.gridLayout.addItem(spacerItem, 0, 2, 1, 1)
        self.horizontalLayout.addWidget(self.options)
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
        self.publish_toolbar = PublishToolBar(parent=MainWindow)
        self.publish_toolbar.setObjectName("publish_toolbar")
        MainWindow.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.publish_toolbar)
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
        icon = QtGui.QIcon.fromTheme("text-x-script")
        self.action_LaTeX.setIcon(icon)
        self.action_LaTeX.setObjectName("action_LaTeX")
        self.action_Pdf = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("x-office-document")
        self.action_Pdf.setIcon(icon)
        self.action_Pdf.setObjectName("action_Pdf")
        self.action_Add_MCQ_Editor_to_start_menu = QtGui.QAction(parent=MainWindow)
        self.action_Add_MCQ_Editor_to_start_menu.setObjectName("action_Add_MCQ_Editor_to_start_menu")
        self.actionFind = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("edit-find")
        self.actionFind.setIcon(icon)
        self.actionFind.setObjectName("actionFind")
        self.actionReplace = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("edit-find-replace")
        self.actionReplace.setIcon(icon)
        self.actionReplace.setObjectName("actionReplace")
        self.actionNone = QtGui.QAction(parent=MainWindow)
        self.actionNone.setObjectName("actionNone")
        self.action_Send_Qscintilla_Command = QtGui.QAction(parent=MainWindow)
        self.action_Send_Qscintilla_Command.setObjectName("action_Send_Qscintilla_Command")
        self.action_Close = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("window-close")
        self.action_Close.setIcon(icon)
        self.action_Close.setObjectName("action_Close")
        self.action_Empty_file = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("text-x-generic")
        self.action_Empty_file.setIcon(icon)
        self.action_Empty_file.setObjectName("action_Empty_file")
        self.action_Mcq_ptyx_file = QtGui.QAction(parent=MainWindow)
        self.action_Mcq_ptyx_file.setObjectName("action_Mcq_ptyx_file")
        self.action_Update_imports = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("view-refresh")
        self.action_Update_imports.setIcon(icon)
        self.action_Update_imports.setObjectName("action_Update_imports")
        self.action_Add_folder = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("list-add")
        self.action_Add_folder.setIcon(icon)
        self.action_Add_folder.setObjectName("action_Add_folder")
        self.action_Open_file_from_current_import_line = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("go-jump")
        self.action_Open_file_from_current_import_line.setIcon(icon)
        self.action_Open_file_from_current_import_line.setObjectName("action_Open_file_from_current_import_line")
        self.actionN_ew_Session = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("window-new")
        self.actionN_ew_Session.setIcon(icon)
        self.actionN_ew_Session.setObjectName("actionN_ew_Session")
        self.actionComment = QtGui.QAction(parent=MainWindow)
        self.actionComment.setObjectName("actionComment")
        self.actionTest = QtGui.QAction(parent=MainWindow)
        self.actionTest.setObjectName("actionTest")
        self.actionPublish = QtGui.QAction(parent=MainWindow)
        icon = QtGui.QIcon.fromTheme("emblem-documents")
        self.actionPublish.setIcon(icon)
        self.actionPublish.setObjectName("actionPublish")
        self.action_Launch_scan = QtGui.QAction(parent=MainWindow)
        self.action_Launch_scan.setObjectName("action_Launch_scan")
        self.actionFormat_python_code = QtGui.QAction(parent=MainWindow)
        self.actionFormat_python_code.setObjectName("actionFormat_python_code")
        self.menu_Recent_Files.addAction(self.actionNone)
        self.menu_New.addAction(self.action_Empty_file)
        self.menu_New.addAction(self.action_Mcq_ptyx_file)
        self.menuFichier.addAction(self.menu_New.menuAction())
        self.menuFichier.addAction(self.menu_Recent_Files.menuAction())
        self.menuFichier.addAction(self.action_Open)
        self.menuFichier.addAction(self.action_Save)
        self.menuFichier.addAction(self.actionSave_as)
        self.menuFichier.addAction(self.action_Close)
        self.menuFichier.addSeparator()
        self.menuFichier.addAction(self.actionN_ew_Session)
        self.menuFichier.addSeparator()
        self.menuFichier.addAction(self.action_Quitter)
        self.menuCompilation.addAction(self.action_LaTeX)
        self.menuCompilation.addAction(self.action_Pdf)
        self.menuCompilation.addAction(self.actionPublish)
        self.menu_Tools.addAction(self.action_Add_MCQ_Editor_to_start_menu)
        self.menu_Edit.addAction(self.actionFind)
        self.menu_Edit.addAction(self.actionReplace)
        self.menuDebug.addAction(self.action_Send_Qscintilla_Command)
        self.menuImports.addAction(self.action_Update_imports)
        self.menuImports.addAction(self.action_Add_folder)
        self.menuImports.addAction(self.action_Open_file_from_current_import_line)
        self.menu_Code.addAction(self.actionComment)
        self.menu_Code.addAction(self.menuImports.menuAction())
        self.menu_Code.addAction(self.actionFormat_python_code)
        self.menuScan.addAction(self.action_Launch_scan)
        self.menubar.addAction(self.menuFichier.menuAction())
        self.menubar.addAction(self.menu_Edit.menuAction())
        self.menubar.addAction(self.menu_Code.menuAction())
        self.menubar.addAction(self.menuCompilation.menuAction())
        self.menubar.addAction(self.menuScan.menuAction())
        self.menubar.addAction(self.menu_Tools.menuAction())
        self.menubar.addAction(self.menuDebug.menuAction())
        self.menubar.addAction(self.menu_help.menuAction())
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
        self.menu_New.setTitle(_translate("MainWindow", "&New"))
        self.menuCompilation.setTitle(_translate("MainWindow", "&Make"))
        self.menu_Tools.setTitle(_translate("MainWindow", "&Tools"))
        self.menu_Edit.setTitle(_translate("MainWindow", "&Edit"))
        self.menu_help.setTitle(_translate("MainWindow", "&Help"))
        self.menuDebug.setTitle(_translate("MainWindow", "&Debug"))
        self.menu_Code.setTitle(_translate("MainWindow", "&Code"))
        self.menuImports.setTitle(_translate("MainWindow", "&Imports"))
        self.menuScan.setTitle(_translate("MainWindow", "Scan"))
        self.compilation_dock.setWindowTitle(_translate("MainWindow", "Output"))
        self.search_dock.setWindowTitle(_translate("MainWindow", "Find and replace"))
        self.findLabel.setText(_translate("MainWindow", "Fi&nd"))
        self.replace_label.setText(_translate("MainWindow", "Re&place with"))
        self.options.setTitle(_translate("MainWindow", "&Options"))
        self.selectionOnlyCheckBox.setToolTip(_translate("MainWindow", "<html><head/><body><p>Search only inside currently selected text.</p></body></html>"))
        self.selectionOnlyCheckBox.setText(_translate("MainWindow", "&Selection only"))
        self.caseCheckBox.setText(_translate("MainWindow", "&Case sensitive"))
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
        self.publish_toolbar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.action_Open.setText(_translate("MainWindow", "&Open"))
        self.action_Open.setShortcut(_translate("MainWindow", "Ctrl+O"))
        self.action_Save.setText(_translate("MainWindow", "&Save"))
        self.action_Save.setShortcut(_translate("MainWindow", "Ctrl+S"))
        self.actionSave_as.setText(_translate("MainWindow", "Save &as"))
        self.actionSave_as.setShortcut(_translate("MainWindow", "Ctrl+Shift+S"))
        self.action_Quitter.setText(_translate("MainWindow", "&Quitter"))
        self.action_LaTeX.setText(_translate("MainWindow", "&LaTeX code preview"))
        self.action_LaTeX.setToolTip(_translate("MainWindow", "LaTeX code preview"))
        self.action_LaTeX.setShortcut(_translate("MainWindow", "Shift+F5"))
        self.action_Pdf.setText(_translate("MainWindow", "&Pdf preview"))
        self.action_Pdf.setToolTip(_translate("MainWindow", "Pdf preview"))
        self.action_Pdf.setShortcut(_translate("MainWindow", "F5"))
        self.action_Add_MCQ_Editor_to_start_menu.setText(_translate("MainWindow", "&Add shortcut to MCQ Editor in the applications menu"))
        self.actionFind.setText(_translate("MainWindow", "&Find"))
        self.actionFind.setShortcut(_translate("MainWindow", "Ctrl+F"))
        self.actionReplace.setText(_translate("MainWindow", "&Replace"))
        self.actionReplace.setShortcut(_translate("MainWindow", "Ctrl+H"))
        self.actionNone.setText(_translate("MainWindow", "EMPTY"))
        self.action_Send_Qscintilla_Command.setText(_translate("MainWindow", "&Send Qscintilla Command"))
        self.action_Close.setText(_translate("MainWindow", "&Close"))
        self.action_Close.setShortcut(_translate("MainWindow", "Ctrl+W"))
        self.action_Empty_file.setText(_translate("MainWindow", "&Empty file"))
        self.action_Empty_file.setShortcut(_translate("MainWindow", "Ctrl+N"))
        self.action_Mcq_ptyx_file.setText(_translate("MainWindow", "&Mcq ptyx file"))
        self.action_Mcq_ptyx_file.setShortcut(_translate("MainWindow", "Ctrl+Shift+N"))
        self.action_Update_imports.setText(_translate("MainWindow", "&Update imports"))
        self.action_Update_imports.setShortcut(_translate("MainWindow", "Ctrl+Shift+I"))
        self.action_Add_folder.setText(_translate("MainWindow", "&Add directory"))
        self.action_Add_folder.setShortcut(_translate("MainWindow", "Ctrl+I"))
        self.action_Open_file_from_current_import_line.setText(_translate("MainWindow", "&Open file from current import line"))
        self.action_Open_file_from_current_import_line.setShortcut(_translate("MainWindow", "Ctrl+Shift+O"))
        self.actionN_ew_Session.setText(_translate("MainWindow", "N&ew Session"))
        self.actionComment.setText(_translate("MainWindow", "&Comment"))
        self.actionComment.setShortcut(_translate("MainWindow", "Ctrl+M"))
        self.actionTest.setText(_translate("MainWindow", "Test"))
        self.actionPublish.setText(_translate("MainWindow", "Pu&blish"))
        self.actionPublish.setToolTip(_translate("MainWindow", "Publish"))
        self.actionPublish.setShortcut(_translate("MainWindow", "Ctrl+B"))
        self.action_Launch_scan.setText(_translate("MainWindow", "&Launch scan"))
        self.actionFormat_python_code.setText(_translate("MainWindow", "Format python code"))
        self.actionFormat_python_code.setShortcut(_translate("MainWindow", "Ctrl+Shift+F"))
from ptyx_mcq_editor.files_book import FilesBook
from ptyx_mcq_editor.find_and_replace import FindAndReplaceWidget
from ptyx_mcq_editor.preview.tab_widget import CompilationTabs
from ptyx_mcq_editor.publish.toolbar import PublishToolBar


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())
