###############################################################################
# ICE Explorer: Application for viewing and inspecting ICE cache data.
# Copyright (C) 2010  M.A. Belzile
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from PyQt4 import QtCore, QtGui
import multiprocessing as mp
import ui_prefs
import sys,os

_default_export_folder = r'c:\temp'
if not sys.platform.startswith('win'):
    _default_export_folder = r'/var/tmp'

class ICEPreferences( QtGui.QDialog ):
    
    def __init__( self, parent=None ):
        super( ICEPreferences, self).__init__(parent)
        self.setWindowTitle("Preferences")
        self.ui = ui_prefs.Ui_Preferences()
        self.ui.setupUi( self )        
        self.ui.process_count_edit.setText( str(mp.cpu_count()) )
        self.ui.export_folder_edit.setText( _default_export_folder )
        self.ui.default_export_folder_btn.pressed.connect( self._on_select_default_export_folder )
        
    @property
    def process_count(self):
        return int(self.ui.process_count_edit.text())

    @property
    def export_folder(self):
        return self.ui.export_folder_edit.text()

    def _on_select_default_export_folder(self):
        self.parent().statusBar().clearMessage()
        title = 'Select The Default Export Folder'        
        folder = QtGui.QFileDialog.getExistingDirectory( self, title, self.ui.export_folder_edit.text(), QtGui.QFileDialog.ShowDirsOnly )
        if not folder:
            return
        self.ui.export_folder_edit.setText( folder )        
