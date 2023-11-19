# Form implementation generated from reading ui file 'ui/find_and_replace.ui'
#
# Created by: PyQt6 UI code generator 6.6.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(771, 213)
        self.horizontalLayout = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.texts_fields = QtWidgets.QFormLayout()
        self.texts_fields.setObjectName("texts_fields")
        self.findLabel = QtWidgets.QLabel(parent=Dialog)
        self.findLabel.setObjectName("findLabel")
        self.texts_fields.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.findLabel)
        self.find_field = QtWidgets.QLineEdit(parent=Dialog)
        self.find_field.setObjectName("find_field")
        self.texts_fields.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.find_field)
        self.replace_label = QtWidgets.QLabel(parent=Dialog)
        self.replace_label.setObjectName("replace_label")
        self.texts_fields.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.replace_label)
        self.replace_field = QtWidgets.QLineEdit(parent=Dialog)
        self.replace_field.setObjectName("replace_field")
        self.texts_fields.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.replace_field)
        self.verticalLayout.addLayout(self.texts_fields)
        self.options = QtWidgets.QGroupBox(parent=Dialog)
        self.options.setObjectName("options")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.options)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.selectionOnlyCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.selectionOnlyCheckBox.setObjectName("selectionOnlyCheckBox")
        self.horizontalLayout_2.addWidget(self.selectionOnlyCheckBox)
        self.regexCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.regexCheckBox.setObjectName("regexCheckBox")
        self.horizontalLayout_2.addWidget(self.regexCheckBox)
        self.wholeCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.wholeCheckBox.setObjectName("wholeCheckBox")
        self.horizontalLayout_2.addWidget(self.wholeCheckBox)
        self.caseCheckBox = QtWidgets.QCheckBox(parent=self.options)
        self.caseCheckBox.setObjectName("caseCheckBox")
        self.horizontalLayout_2.addWidget(self.caseCheckBox)
        self.verticalLayout.addWidget(self.options)
        self.information_label = QtWidgets.QLabel(parent=Dialog)
        self.information_label.setText("")
        self.information_label.setObjectName("information_label")
        self.verticalLayout.addWidget(self.information_label)
        self.buttons_field = QtWidgets.QHBoxLayout()
        self.buttons_field.setObjectName("buttons_field")
        spacerItem = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum
        )
        self.buttons_field.addItem(spacerItem)
        self.replace_all_button = QtWidgets.QPushButton(parent=Dialog)
        self.replace_all_button.setObjectName("replace_all_button")
        self.buttons_field.addWidget(self.replace_all_button)
        self.replace_button = QtWidgets.QPushButton(parent=Dialog)
        self.replace_button.setObjectName("replace_button")
        self.buttons_field.addWidget(self.replace_button)
        self.find_button = QtWidgets.QPushButton(parent=Dialog)
        self.find_button.setObjectName("find_button")
        self.buttons_field.addWidget(self.find_button)
        self.verticalLayout.addLayout(self.buttons_field)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.direction = QtWidgets.QGroupBox(parent=Dialog)
        self.direction.setObjectName("direction")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.direction)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.upRadioButton = QtWidgets.QRadioButton(parent=self.direction)
        self.upRadioButton.setObjectName("upRadioButton")
        self.verticalLayout_3.addWidget(self.upRadioButton)
        self.downRadioButton = QtWidgets.QRadioButton(parent=self.direction)
        self.downRadioButton.setChecked(True)
        self.downRadioButton.setObjectName("downRadioButton")
        self.verticalLayout_3.addWidget(self.downRadioButton)
        self.verticalLayout_2.addWidget(self.direction)
        spacerItem1 = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding
        )
        self.verticalLayout_2.addItem(spacerItem1)
        self.horizontalLayout.addLayout(self.verticalLayout_2)
        self.findLabel.setBuddy(self.find_field)
        self.replace_label.setBuddy(self.replace_field)

        self.retranslateUi(Dialog)
        QtCore.QMetaObject.connectSlotsByName(Dialog)
        Dialog.setTabOrder(self.find_field, self.replace_field)
        Dialog.setTabOrder(self.replace_field, self.upRadioButton)
        Dialog.setTabOrder(self.upRadioButton, self.downRadioButton)
        Dialog.setTabOrder(self.downRadioButton, self.caseCheckBox)
        Dialog.setTabOrder(self.caseCheckBox, self.wholeCheckBox)
        Dialog.setTabOrder(self.wholeCheckBox, self.regexCheckBox)
        Dialog.setTabOrder(self.regexCheckBox, self.selectionOnlyCheckBox)
        Dialog.setTabOrder(self.selectionOnlyCheckBox, self.find_button)
        Dialog.setTabOrder(self.find_button, self.replace_button)
        Dialog.setTabOrder(self.replace_button, self.replace_all_button)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Find and replace"))
        self.findLabel.setText(_translate("Dialog", "Fi&nd"))
        self.replace_label.setText(_translate("Dialog", "Re&place with"))
        self.options.setTitle(_translate("Dialog", "&Options"))
        self.selectionOnlyCheckBox.setText(_translate("Dialog", "&Selection only"))
        self.regexCheckBox.setToolTip(
            _translate(
                "Dialog",
                '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0//EN" "http://www.w3.org/TR/REC-html40/strict.dtd">\n'
                '<html><head><meta name="qrichtext" content="1" /><style type="text/css">\n'
                "p, li { white-space: pre-wrap; }\n"
                "</style></head><body style=\" font-family:'Sans'; font-size:10pt; font-weight:400; font-style:normal;\">\n"
                '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">whether the text to search should be interpreted as a regular expression.</p>\n'
                '<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"></p>\n'
                '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">You may want to take a look at the syntax of regular expressions:</p>\n'
                '<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a href="http://doc.trolltech.com/qregexp.html"><span style=" text-decoration: underline; color:#0000ff;">http://doc.trolltech.com/qregexp.html</span></a></p></body></html>',
            )
        )
        self.regexCheckBox.setText(_translate("Dialog", "R&egular Expression"))
        self.wholeCheckBox.setText(_translate("Dialog", "&Whole words only"))
        self.caseCheckBox.setText(_translate("Dialog", "&Case sensitive"))
        self.replace_all_button.setText(_translate("Dialog", "Replace &All"))
        self.replace_button.setText(_translate("Dialog", "&Replace"))
        self.find_button.setText(_translate("Dialog", "&Find"))
        self.direction.setTitle(_translate("Dialog", "D&irection"))
        self.upRadioButton.setText(_translate("Dialog", "&Up"))
        self.downRadioButton.setText(_translate("Dialog", "&Down"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    ui = Ui_Dialog()
    ui.setupUi(Dialog)
    Dialog.show()
    sys.exit(app.exec())