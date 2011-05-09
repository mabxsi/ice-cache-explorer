###############################################################################
# ICE Explorer: A viewer and reader for ICE cache data
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
from icereader import ICEReader
from h5reader import H5Reader
from icereader_util import get_files_from_cache_folder, get_files
from consts import CONSTS 
from process_pool import Pool
import ui_export_folder
import ui_export_file
import sys
import os
import time

class ICEExporter(QtCore.QObject):
    """ Class to manage processes for exporting ICE cache data to ascii. """
    # string: export file name
    cacheExporting = QtCore.pyqtSignal( str ) 
    # int: number of files to export
    beginCacheExporting = QtCore.pyqtSignal( int ) 
    endCacheExporting = QtCore.pyqtSignal( ) 

    # states
    STOP = 0
    RUN = 1
    ERROR = 2
        
    def __init__(self, parent = None):
        super(ICEExporter,self).__init__(parent)
        self.files = []
        self.state = self.STOP
        self.destination_folder = '.'
        self.t1 = 0
        self.t2 = 0
        self.fmt = CONSTS.TEXT_FMT
        self.pool = Pool(self)
        
        # dialogs
        self._folder_dialog = ICEExportFolderDialog(self, parent)
        self._file_dialog = ICEExportFileDialog(self, parent)

    @property
    def folder_dialog( self ):
        return self._folder_dialog

    @property
    def file_dialog( self ):
        return self._file_dialog
    
    def cancel(self):
        self.pool.cancel()

    def export_folder( self, folder, destination, fmt=CONSTS.TEXT_FMT ):    
        """ Export the cache files contained in a folder """
        (self.files,startindex,end) = get_files_from_cache_folder( folder )
        self.destination_folder = destination
        self.state = self.STOP
        self.files_processed = 0
        self.t1 = 0
        self.t2 = 0
        self.fmt = fmt
        self._start()

    def export_files( self, files, destination, fmt=CONSTS.TEXT_FMT):    
        """ Export a list of cache files """
        (self.files,startindex,end) = get_files(files)
        self.destination_folder = destination
        self.state = self.STOP
        self.t1 = 0
        self.t2 = 0
        self.fmt = fmt
        self._start()

    def _start( self ):
        """ Start file export process. """ 
        self.file_block = 1
        self.indexset = range( 0, len(self.files), self.file_block ) 

        # Submit export tasks to process pool
        cpu_count = 1
        if self.parent():
            cpu_count = self.parent().prefs.process_count
        else:
            import multiprocessing as mp
            cpu_count = mp.cpu_count() 
            
        self.pool.init( cpu_count, self._on_process_callback )
        self.state = self.STOP
        file_count = len(self.files)
        self.files_processed = 0
        for i in self.indexset:
            file_list = []
            for j in range(self.file_block):
                if i+j < file_count:
                    file_list.append( self.files[i+j] )                
            self.pool.submit( ExportTask( [file_list, self.destination_folder, self.fmt] ) )            

    def _on_process_callback( self, sender, notif, arg ):
        """ Called when an event occurs from a process """
        
        if notif == Pool.STARTED:
            #print 'Pool.STARTED'
            if self.state == self.STOP:
                self.t1 = time.time()
                self.beginCacheExporting.emit( len(self.files) )
                self.state = self.RUN
                
        elif notif == Pool.ERROR:
            print 'process error: %d - %s' % (sender.pid(), arg)
            self.endCacheExporting.emit( )
            self.state = self.ERROR
            
        elif notif == Pool.STATE_CHANGE:
            pass
            
        elif notif == Pool.OUTPUT_MSG:
            if self.state == self.ERROR:
                return
            s_out = bytes.decode( bytes( sender.readAllStandardOutput() ) )
            #print 'Pool.OUTPUT_MSG: %s' % s_out
            self.cacheExporting.emit( s_out )            
                
        elif notif == Pool.OUTPUT_ERROR_MSG:
            s_out = bytes.decode( bytes( sender.readAllStandardError() ) )
            print 'process error output: %s - %s\nRetry your operation.' % ((repr(sender)),s_out)
                
        elif notif == Pool.FINISHED:
            #print 'Pool.FINISHED'

            if self.state == self.ERROR:
                return
            self.files_processed += self.file_block
            if self.files_processed >= len(self.files):
                self.t2 = time.time()
                self.endCacheExporting.emit( )            
                self.state = self.STOP
                print 'Export time %0.3f s' % (self.t2-self.t1)
        
class ExportTask(object):
    """ Task to export cache files from a process """
    def __init__(self,args):        
        """ 
        Process arguments:
        arg0: list of files
        arg1: target export folder
        arg2: export format {TEXT|SIH5}
        """ 
        self._cmd = 'python.exe export_process.py "%s" %s %d' % (repr(args[0]),args[1],int(args[2]))

    def __call__(self):
        """ Returns the process command """
        return self._cmd

class ICEExportFolderDialog( QtGui.QDialog ):
    """Dialog for exporting folder data to text or hdf5 format"""
    def __init__( self, exporter, parent=None ):
        super( ICEExportFolderDialog, self ).__init__(parent)
        #self.setWindowTitle("Export Folder Dialog")
                
        self.fmt = None
        self.exporter = exporter
        
        self.ui = ui_export_folder.Ui_ExportFolder()
        self.ui.setupUi( self )
        self.ui.src_folder_btn.pressed.connect( self._on_select_folder_to_export )
        self.ui.dst_folder_btn.pressed.connect( self._on_select_dest_folder )

    def open( self, fmt ):
        self.fmt = fmt

        if self.fmt == CONSTS.SIH5_FMT:
            title = 'Export Cache Folder to SIH5 Format'
        else:
            title = 'Export Cache Folder to Text Format'
        self.setWindowTitle( title )
        
        self.ui.dst_folder_edit.setText( self.parent().prefs.export_folder )
        retval = self.exec_()
        
        if retval == QtGui.QDialog.Accepted:
            self.exporter.export_folder( self.ui.src_folder_edit.text(), self.ui.dst_folder_edit.text(), self.fmt )                
                
    def _on_select_folder_to_export(self):
        self.parent().statusBar().clearMessage()
        title = 'Select Cache Folder to Export'        
        folder = QtGui.QFileDialog.getExistingDirectory( self, title, '', QtGui.QFileDialog.ShowDirsOnly )
        if not folder:
            return
        self.ui.src_folder_edit.setText( folder )        

    def _on_select_dest_folder(self):
        self.parent().statusBar().clearMessage()
        title = 'Select Destination Folder'            
        folder = QtGui.QFileDialog.getExistingDirectory( self, title, self.ui.dst_folder_edit.text(), QtGui.QFileDialog.ShowDirsOnly )
        if not folder:
            return
        self.ui.dst_folder_edit.setText( folder )        

class ICEExportFileDialog( QtGui.QDialog ):
    """Dialog for exporting data file(s) to text or hdf5 format"""
    def __init__( self, exporter, parent=None ):
        super( ICEExportFileDialog, self ).__init__(parent)
        #self.setWindowTitle("Export Folder Dialog")
                
        self.fmt = None
        self.exporter = exporter
        
        self.ui = ui_export_file.Ui_ExportFile()
        self.ui.setupUi( self )
        self.ui.dst_folder_btn.pressed.connect( self._on_select_dest_folder )

    def open( self, files, fmt ):
        self.fmt = fmt

        if self.fmt == CONSTS.SIH5_FMT:
            title = 'Export Cache Folder to SIH5 Format'
        else:
            title = 'Export Cache Folder to Text Format'
        self.setWindowTitle( title )
        
        self.ui.dst_folder_edit.setText( self.parent().prefs.export_folder )
        retval = self.exec_()
        
        if retval == QtGui.QDialog.Accepted:
            self.exporter.export_files( files, self.ui.dst_folder_edit.text(), self.fmt )                
                
    def _on_select_dest_folder(self):
        self.parent().statusBar().clearMessage()
        title = 'Select Destination Folder'            
        folder = QtGui.QFileDialog.getExistingDirectory( self, title, self.ui.dst_folder_edit.text(), QtGui.QFileDialog.ShowDirsOnly )
        if not folder:
            return
        self.ui.dst_folder_edit.setText( folder )        

def test_export_file():
    exporter = ICEExporter( ) 
    exporter.export_files([r'C:\dev\icecache_data\cache50\29.icecache'], r'c:\temp', fmt=CONSTS.SIH5_FMT)                
    
if __name__ == '__main__':
    test_export_file()
