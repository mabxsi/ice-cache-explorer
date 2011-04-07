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
from icereader import *

PACKET_LEN = struct.calcsize('L')  # 4 bytes
SERVER = 'ICE-CACHE-LOADER'
CLIB = ctypes.cdll.LoadLibrary(ctypes.util.find_library('c'))
TIMEOUT = 5000

theApp = QtCore.QCoreApplication(sys.argv)

def load_data_from_file( filename, index ):                        
    """ create a reader lo load acache file and returns the data read. """
    reader = ICEReader( filename )    
    try:
        reader.load( )
    except:
        # something is wrong, probably a bad file format 
        return ( None, filename, [], [], [] )

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
    
    return ( index, filename, points, colors, sizes )

def main(argv):
    
    files = eval(argv[1])
    indices = eval(argv[2])

    # export input files
    for i,f in enumerate(files):
        data = load_data_from_file( f, indices[i] )

        socket = QtNetwork.QLocalSocket(theApp)
        if socket == None:
            sys.stderr.write("Error creating socket")
            sys.stderr.flush()        
            return 
    
        socket.connectToServer(SERVER)
        if not socket.waitForConnected(TIMEOUT):
            sys.stderr.write( 'Process error server connection: %s\n' % socket.errorString() )
            sys.stderr.flush()        
            return 

        # request the server to allocate memory of size data_bytes_count
        data_bytes = pickle.dumps( data, 2)
        data_bytes_len = len(data_bytes)        
        req_bytes = pickle.dumps( [f, data_bytes_len], 2)
        req_bytes_len = len(req_bytes)
        
        socket.write(struct.pack('L',req_bytes_len))
        if not socket.waitForBytesWritten(TIMEOUT):
            sys.stderr.write('Process error while waiting for request byte length to be written: %s\n' % socket.errorString() )
            sys.stderr.flush()
            return

        socket.write(req_bytes)
        if not socket.waitForBytesWritten(TIMEOUT):
            sys.stderr.write('Process error while waiting for request bytes to be written: %s\n' % socket.errorString() )
            sys.stderr.flush()
            return

        if not socket.waitForReadyRead(TIMEOUT):
            sys.stderr.write('Process error while waiting for acknowledge: %s\n' % socket.errorString() )
            sys.stderr.flush()
            return

        ack = socket.readLine()
        
        socket.disconnectFromServer()
        del socket

        # get the shared memory segment
        shmem = QtCore.QSharedMemory( f )
    
        if not shmem.isAttached() and not shmem.attach():
            sys.stderr.write('Process error shared memory access: %s\n' % str(sys.exc_info()[1]) )
            sys.stderr.flush()        
            return             
            
        shmem.lock()
        try:
            CLIB.memcpy(int(shmem.data()), data_bytes, data_bytes_len)
        except:
            sys.stderr.write('Process error copying bytes to shared memory: %s\n' % str(sys.exc_info()[1]) )
            sys.stderr.flush()            
        finally:
            shmem.unlock()
        
        # signal server we are done with this file 
        sys.stdout.write( f )
        sys.stdout.flush()  
   
if __name__ == '__main__':
    main(sys.argv)
