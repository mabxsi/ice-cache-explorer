# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'prefs.ui'
#
# Created: Sun May 08 22:05:12 2011
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Preferences(object):
    def setupUi(self, Preferences):
        Preferences.setObjectName(_fromUtf8("Preferences"))
        Preferences.resize(416, 113)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("resources/preferences.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        Preferences.setWindowIcon(icon)
        self.buttonBox = QtGui.QDialogButtonBox(Preferences)
        self.buttonBox.setGeometry(QtCore.QRect(324, 71, 81, 32))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.process_count_edit = QtGui.QLineEdit(Preferences)
        self.process_count_edit.setGeometry(QtCore.QRect(132, 12, 238, 20))
        self.process_count_edit.setObjectName(_fromUtf8("process_count_edit"))
        self.label = QtGui.QLabel(Preferences)
        self.label.setGeometry(QtCore.QRect(22, 12, 101, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_2 = QtGui.QLabel(Preferences)
        self.label_2.setGeometry(QtCore.QRect(22, 38, 65, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.export_folder_edit = QtGui.QLineEdit(Preferences)
        self.export_folder_edit.setGeometry(QtCore.QRect(132, 38, 238, 20))
        self.export_folder_edit.setObjectName(_fromUtf8("export_folder_edit"))
        self.default_export_folder_btn = QtGui.QPushButton(Preferences)
        self.default_export_folder_btn.setGeometry(QtCore.QRect(383, 35, 21, 23))
        self.default_export_folder_btn.setContextMenuPolicy(QtCore.Qt.PreventContextMenu)
        self.default_export_folder_btn.setObjectName(_fromUtf8("default_export_folder_btn"))

        self.retranslateUi(Preferences)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Preferences.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Preferences.reject)
        QtCore.QMetaObject.connectSlotsByName(Preferences)

    def retranslateUi(self, Preferences):
        Preferences.setWindowTitle(QtGui.QApplication.translate("Preferences", "Preferences", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Preferences", "Number of Processes", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Preferences", "Export Folder", None, QtGui.QApplication.UnicodeUTF8))
        self.default_export_folder_btn.setText(QtGui.QApplication.translate("Preferences", "...", None, QtGui.QApplication.UnicodeUTF8))

