# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'export_file.ui'
#
# Created: Sun May 08 21:52:19 2011
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ExportFile(object):
    def setupUi(self, ExportFile):
        ExportFile.setObjectName(_fromUtf8("ExportFile"))
        ExportFile.resize(325, 123)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("resources/export-cache.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        ExportFile.setWindowIcon(icon)
        self.ExportButton = QtGui.QDialogButtonBox(ExportFile)
        self.ExportButton.setGeometry(QtCore.QRect(80, 78, 171, 32))
        self.ExportButton.setOrientation(QtCore.Qt.Horizontal)
        self.ExportButton.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.ExportButton.setCenterButtons(True)
        self.ExportButton.setObjectName(_fromUtf8("ExportButton"))
        self.dest = QtGui.QGroupBox(ExportFile)
        self.dest.setGeometry(QtCore.QRect(10, 18, 301, 51))
        self.dest.setObjectName(_fromUtf8("dest"))
        self.dst_folder_btn = QtGui.QPushButton(self.dest)
        self.dst_folder_btn.setGeometry(QtCore.QRect(270, 20, 21, 23))
        self.dst_folder_btn.setObjectName(_fromUtf8("dst_folder_btn"))
        self.dst_folder_edit = QtGui.QLineEdit(self.dest)
        self.dst_folder_edit.setGeometry(QtCore.QRect(20, 20, 241, 20))
        self.dst_folder_edit.setObjectName(_fromUtf8("dst_folder_edit"))

        self.retranslateUi(ExportFile)
        QtCore.QObject.connect(self.ExportButton, QtCore.SIGNAL(_fromUtf8("accepted()")), ExportFile.accept)
        QtCore.QObject.connect(self.ExportButton, QtCore.SIGNAL(_fromUtf8("rejected()")), ExportFile.reject)
        QtCore.QMetaObject.connectSlotsByName(ExportFile)

    def retranslateUi(self, ExportFile):
        ExportFile.setWindowTitle(QtGui.QApplication.translate("ExportFile", "Export Cache File(s)", None, QtGui.QApplication.UnicodeUTF8))
        self.dest.setTitle(QtGui.QApplication.translate("ExportFile", "Destination Folder", None, QtGui.QApplication.UnicodeUTF8))
        self.dst_folder_btn.setText(QtGui.QApplication.translate("ExportFile", "...", None, QtGui.QApplication.UnicodeUTF8))

