###############################################################################
# ICE Cache Explorer: A viewer and reader for ICE cache data
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

from PyQt4 import QtCore
from icereader import ICEReader, get_files_from_cache_folder, get_files
from process_pool import Pool
import sys
import time

class ICEExporter(QtCore.QObject):
    """ Class to manage processes for exporting ICE cache data to ascii. """
    # string: export file name
    cacheExporting = QtCore.pyqtSignal( str ) 
    # int: number of files to export
    beginCacheExporting = QtCore.pyqtSignal( int ) 
    endCacheExporting = QtCore.pyqtSignal( ) 

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
        self.pool = Pool(self)
        
    def cancel(self):
        self.pool.cancel()

    def export_folder( self, folder, destination, supported_attributes ):    
        """ Export the cache files contained in a folder """
        (self.files,startindex,end) = get_files_from_cache_folder( folder )
        self.destination_folder = destination
        self.supported_attributes = supported_attributes
        self.state = self.STOP
        self.files_processed = 0
        self.t1 = 0
        self.t2 = 0
        self._start()

    def export_files( self, files, destination, supported_attributes ):    
        """ Export a list of cache files """
        (self.files,startindex,end) = get_files(files)
        self.destination_folder = destination
        self.supported_attributes = supported_attributes
        self.state = self.STOP
        self.t1 = 0
        self.t2 = 0
        self._start()
       
    def _start(self):
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
            self.pool.submit( ExportTask( [ file_list, self.destination_folder ] ) )

    def _on_process_callback( self, sender, notif, arg ):
        """ Called when an event occurs from a process """
        
        if notif == Pool.STARTED:
            if self.state == self.STOP:
                self.t1 = time.time()
                self.beginCacheExporting.emit( len(self.files) )
                self.state = self.RUN
                
        elif notif == Pool.ERROR:
            self.endCacheExporting.emit( )
            self.state = self.ERROR
            
        elif notif == Pool.STATE_CHANGE:
            pass
            
        elif notif == Pool.OUTPUT_MSG:
            try:      
                if self.state == self.ERROR:
                    return
                s_out = bytes.decode( bytes( sender.readAllStandardOutput() ) )
                self.cacheExporting.emit( s_out )            
            except:
                print '_on_process_output - error: %s' % sys.exc_info()[0]
                
        elif notif == Pool.OUTPUT_ERROR:
            try:            
                print 'Output error from process %d' % sender.pid()
            except:
                print '_on_process_error_output error: %s' % sys.exc_info()[0]
                
        elif notif == Pool.FINISHED:
            try:            
                if self.state == self.ERROR:
                    return                
                self.files_processed += self.file_block
                if self.files_processed >= len(self.files):
                    self.t2 = time.time()
                    self.endCacheExporting.emit( )            
                    self.state = self.STOP
                    print 'Export time %0.3f s' % (self.t2-self.t1)
            except:
                print '_on_process_finished error: %s' % sys.exc_info()[0]


class ExportTask(object):
    """ Task to export cache files from a process """
    def __init__(self,args):        
        """ 
        Process arguments:
        arg0: list of files
        arg1: target export folder
        """ 
        self._cmd = 'python.exe export_process.py "%s" %s' % (repr(args[0]),args[1])

    def __call__(self):
        """ Returns the process command """
        return self._cmd

def test_export_file():
    exporter = ICEExporter( ) 
    exporter.export_files([r'C:\dev\icecache_data\cache50\25.icecache'], r'c:\temp', ())                
    
if __name__ == '__main__':
    test_export_file()
