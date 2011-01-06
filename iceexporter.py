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
from icereader import ICEReader, get_files_from_cache_folder
import re

class ICEExporter(QtCore.QThread):
    """ Worker thread for exporting ICE cache data to ascii. """
    # signal sent for each cache exported
    # int: cache index
    # object: reader
    cacheExported = QtCore.pyqtSignal( int, object ) 

    def __init__(self, parent = None):
        super(ICEExporter,self).__init__(parent)
        self.exiting = False
        self.files = []
        self.startindex = 1
        self.destination_folder = '.'
        
    def __del__(self):    
        self.exiting = True
        self.wait()

    def export_folder( self, folder, destination, supported_attributes ):    
        """ start exporting cache files """
        (self.files,self.startindex,end) = get_files_from_cache_folder( folder )
        self.destination_folder = destination
        self.supported_attributes = supported_attributes
        
        # kick-off thread
        self.start()

    def export_file( self, file, destination, supported_attributes ):    
        """ start exporting cache files """

        self.files = [ file ]
        self.startindex = int(re.findall(r'\d+',file)[-1])
        self.destination_folder = destination
        self.supported_attributes = supported_attributes
        
        # kick-off thread
        self.start()

    def run(self):
        """ Called by the python when the thread has started. """
        n = len(self.files)
        index = self.startindex
        i = 0

        while not self.exiting and n > 0:            
            reader = ICEReader( self.files[i] )    
            reader.load_data( self.supported_attributes )
            reader.log_info( self.destination_folder )

            """ Tell  clients that a cache has been exported """
            self.cacheExported.emit( index, reader )

            i += 1
            index += 1
            n -= 1

            del reader
