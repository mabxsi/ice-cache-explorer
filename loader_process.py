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

from PyQt4 import QtCore, QtNetwork
import ctypes
import ctypes.util
import pickle
import sys
import numpy as np
import struct
import icereader as icer
import h5reader as h5r
from consts import CONSTS
import os

PACKET_LEN = struct.calcsize('L')  # 4 bytes
SERVER = 'ICE-CACHE-LOADER'
CLIB = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
TIMEOUT = 5000

theApp = QtCore.QCoreApplication(sys.argv)

def handle_file( filename, index ):                        
    """ cache file handling. """
    if h5r.is_valid_file( filename ):
        # SIH5 file: nothing to do, the file will be loaded later
        return ( index, filename )

    if icer.is_valid_file( filename ):        
        # load .icecache and save to SIH5 folder
        data_folder = os.path.join( os.path.dirname( filename ), '.sih5' )
        if not os.path.exists( data_folder ):
            os.mkdir( data_folder, 777 )

        # export only if file doesn't exist
        reader = icer.ICEReader( filename )
        reader.export( data_folder, CONSTS.SIH5_FMT, force = False )
        return ( index, reader.export_filename )

    # unsupported file format 
    return ( None, None )    

def main(argv):
    
    files = eval(argv[1])
    indices = eval(argv[2])

    for i,f in enumerate(files):
        data = handle_file( f, indices[i] )

        # tell process about the new file
        sys.stdout.write( str(data) )
        sys.stdout.flush()  
   
if __name__ == '__main__':
    main(sys.argv)
