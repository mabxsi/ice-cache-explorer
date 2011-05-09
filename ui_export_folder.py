# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'export_folder.ui'
#
# Created: Sun May 08 22:07:17 2011
#      by: PyQt4 UI code generator 4.8.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_ExportFolder(object):
    def setupUi(self, ExportFolder):
        ExportFolder.setObjectName(_fromUtf8("ExportFolder"))
        ExportFolder.resize(325, 185)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8("resources/export-cache-folder.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        ExportFolder.setWindowIcon(icon)
        self.ExportButton = QtGui.QDialogButtonBox(ExportFolder)
        self.ExportButton.setGeometry(QtCore.QRect(80, 140, 171, 32))
        self.ExportButton.setOrientation(QtCore.Qt.Horizontal)
        self.ExportButton.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.ExportButton.setCenterButtons(True)
        self.ExportButton.setObjectName(_fromUtf8("ExportButton"))
        self.src = QtGui.QGroupBox(ExportFolder)
        self.src.setGeometry(QtCore.QRect(10, 20, 301, 51))
        self.src.setObjectName(_fromUtf8("src"))
        self.src_folder_btn = QtGui.QPushButton(self.src)
        self.src_folder_btn.setGeometry(QtCore.QRect(270, 20, 21, 23))
        self.src_folder_btn.setObjectName(_fromUtf8("src_folder_btn"))
        self.src_folder_edit = QtGui.QLineEdit(self.src)
        self.src_folder_edit.setGeometry(QtCore.QRect(20, 20, 241, 20))
        self.src_folder_edit.setObjectName(_fromUtf8("src_folder_edit"))
        self.dest = QtGui.QGroupBox(ExportFolder)
        self.dest.setGeometry(QtCore.QRect(10, 80, 301, 51))
        self.dest.setObjectName(_fromUtf8("dest"))
        self.dst_folder_btn = QtGui.QPushButton(self.dest)
        self.dst_folder_btn.setGeometry(QtCore.QRect(270, 20, 21, 23))
        self.dst_folder_btn.setObjectName(_fromUtf8("dst_folder_btn"))
        self.dst_folder_edit = QtGui.QLineEdit(self.dest)
        self.dst_folder_edit.setGeometry(QtCore.QRect(20, 20, 241, 20))
        self.dst_folder_edit.setObjectName(_fromUtf8("dst_folder_edit"))

        self.retranslateUi(ExportFolder)
        QtCore.QObject.connect(self.ExportButton, QtCore.SIGNAL(_fromUtf8("accepted()")), ExportFolder.accept)
        QtCore.QObject.connect(self.ExportButton, QtCore.SIGNAL(_fromUtf8("rejected()")), ExportFolder.reject)
        QtCore.QMetaObject.connectSlotsByName(ExportFolder)

    def retranslateUi(self, ExportFolder):
        ExportFolder.setWindowTitle(QtGui.QApplication.translate("ExportFolder", "Export Cache Folder", None, QtGui.QApplication.UnicodeUTF8))
        self.src.setTitle(QtGui.QApplication.translate("ExportFolder", "Source Folder", None, QtGui.QApplication.UnicodeUTF8))
        self.src_folder_btn.setText(QtGui.QApplication.translate("ExportFolder", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.dest.setTitle(QtGui.QApplication.translate("ExportFolder", "Destination Folder", None, QtGui.QApplication.UnicodeUTF8))
        self.dst_folder_btn.setText(QtGui.QApplication.translate("ExportFolder", "...", None, QtGui.QApplication.UnicodeUTF8))

