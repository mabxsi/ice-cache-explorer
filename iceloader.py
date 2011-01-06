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
import time
from icereader import ICEReader

class ICECacheLoader(QtCore.QThread):
    """ Worker thread for loading cache files to ensures that callers (eg UI) are still responsive during a lenghtly load process. """
    # signal sent for each new loaded cache
    # int: cache index
    # tuple: (reader, points, colors, sizes)
    cacheLoaded = QtCore.pyqtSignal( int, tuple ) 

    def __init__(self, parent = None):    
        super(ICECacheLoader,self).__init__(parent)
        self.exiting = False
        self.files = []
        self.supported_attributes = ()
        
    def __del__(self):    
        self.exiting = True
        self.wait()

    def load_cache_files( self, files, start, end, supported_attributes ):    
        """ start loading cache files """
        self.files = files
        self.supported_attributes = supported_attributes
        self.startindex = start
        self.endindex = end
        
        # kick-off thread
        self.start()

    def __load_data_from_file__( self, cache, filename ):                        
        """ create a reader lo load a given cache file and returns a tuple contianing the reader and the data. """
        reader = ICEReader( filename )    
        reader.load_data( self.supported_attributes )

        points = []
        colors = []
        sizes = []
        
        # Support these parameters only for now        
        if 'PointPosition___' in reader._data:
            points = reader[ 'PointPosition___' ]
        if 'Color___' in reader._data:
            if len(reader[ 'Color___' ]):
                colors = reader[ 'Color___' ]
        if 'Size___' in reader._data:
            if len(reader[ 'Size___' ]):
                sizes = reader[ 'Size' ]

        return ( reader, points, colors, sizes )

    def run(self):
        """ Called by the python thread when a thread has started. """
        n = len(self.files)
        index = self.startindex
        i = 0

        load_start_time = time.clock()        

        while not self.exiting and n > 0:
            data = self.__load_data_from_file__( index, self.files[i] )            
            
            """ Tell interested clients that a new cache has been loaded """
            self.cacheLoaded.emit( index, data )

            i += 1
            index += 1
            n -= 1
