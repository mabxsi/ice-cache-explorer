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
import re

class ICEExporter(QtCore.QThread):
    """ Worker thread for exporting ICE cache data to ascii. """
    # string: export file name
    cacheExporting = QtCore.pyqtSignal( str ) 
    # int: number of files to export
    beginCacheExporting = QtCore.pyqtSignal( int ) 
    endCacheExporting = QtCore.pyqtSignal( ) 

    def __init__(self, parent = None):
        super(ICEExporter,self).__init__(parent)
        self.exiting = False
        self.files = []
        self.startindex = 1
        self.destination_folder = '.'
        
    def __del__(self):    
        self.exiting = True
        self.wait()

    def cancel(self):
        self.exiting = True
        self.wait()

    def export_folder( self, folder, destination, supported_attributes ):    
        """ start exporting cache files """
        self.cancel()
        self.exiting = False
        (self.files,self.startindex,end) = get_files_from_cache_folder( folder )
        self.destination_folder = destination
        self.supported_attributes = supported_attributes
        
        # kick-off thread
        self.start()

    def export_files( self, files, destination, supported_attributes ):    
        """ start exporting cache files """

        self.cancel()
        self.exiting = False
        (self.files,self.startindex,end) = get_files(files)
        self.destination_folder = destination
        self.supported_attributes = supported_attributes
        
        # kick-off thread
        self.start()

    def run(self):
        """ Called by the python when the thread has started. """
        n = len(self.files)
        index = self.startindex
        i = 0

        self.beginCacheExporting.emit( n )

        while not self.exiting and i<n:            
            reader = ICEReader( self.files[i] )                
            reader.load( self.supported_attributes )
            export_filepath = reader.get_export_file_path( self.destination_folder )

            self.cacheExporting.emit( export_filepath )

            reader.export( export_filepath )

            i += 1
            index += 1
            #n -= 1

            del reader

        self.endCacheExporting.emit( )
