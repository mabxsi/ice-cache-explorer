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
import time
import sys
import os
import pickle
from process_pool import Pool

import struct

PACKET_LEN = struct.calcsize('L')  # 4 bytes
SERVER = 'ICE-CACHE-LOADER'
TIMEOUT = 5000

class ICECacheLoader(QtCore.QObject):
    """ Class for loading cache files. Files are loaded through processes managed by the Pool class. The data loaded
    by processes is sent to ICECacheLoader via PyQt's QLocalSocket and QLocalServer which are basically a named pipe. """
    # signal sent for each new loaded cache
    # int: cache index
    # tuple: (reader, points, colors, sizes)
    cacheLoaded = QtCore.pyqtSignal( int, tuple ) 
    beginCacheLoading = QtCore.pyqtSignal()
    endCacheLoading = QtCore.pyqtSignal()

    # Loading state
    STOP = 0
    RUN = 1
    ERROR = 2
    
    def __init__(self, parent = None):    
        super(ICECacheLoader,self).__init__(parent)
        self.pool = None
        self.server = None
        self.shmem = {}
        self.state = self.STOP
        self.files = []
        
    def init_process_server( self ):
        self.shmem = {}
        self.state = self.STOP
        self.files = []
        self.server = QtNetwork.QLocalServer( )
        self.server.newConnection.connect( self._on_new_connection )
        self.pool = Pool(self)
        self.pool.init(self.parent().prefs.process_count, self._on_process_callback)

    def cancel(self):
        self.state = self.STOP
        self.endCacheLoading.emit()        
        if self.pool:
            self.pool.cancel()
        for key in self.shmem.keys():
            self.shmem[ key ].detach()
            self.shmem.pop( key, None )
        
        if self.server:
            self.server.close()
        print "Operation was cancelled."
        
    def load_cache_files( self, files, start, end ):    
        """ Start the loading process. """         
        # initialize the process server first
        self.init_process_server()

        self.files = files
        self.startindex = start
        self.endindex = end        

        # file_block can be used to assing multiple files per process. 
        # note: Normally this would make poor load-balancing and affect performance load
        self.file_block = 1
        self.indexset = range(0,len(self.files),self.file_block)     

        # Submit all load tasks to the process pool
        # note: 1 file / task gives very good performance in general.
        self.state = self.STOP
        file_count = len(self.files)
        self.files_processed = 0
        index = self.startindex
        for i in self.indexset:
            file_list = []
            file_index = []
            for j in range(self.file_block):
                if i+j < file_count:
                    file_list.append( self.files[i+j] )
                    file_index.append( index )
                    index += 1                    
            self.pool.submit( LoaderTask( [ file_list, file_index ] ) )

        # start server
        if self.server.isListening() == False:
            print "Loading in-progress..."
            self.server.listen( SERVER )

    def _on_new_connection( self ):
        """ 
        Handle all loading process connections. 
        Processes and the ICELoader use a shared memory block for copying/reading the loaded data. 
        """
        socket = self.server.nextPendingConnection()
        if not socket.waitForReadyRead(TIMEOUT):
            print 'nextPendingConnection : %s' % socket.errorString()
            return

        # expect a memory creation request
        if socket.peek(PACKET_LEN).length() < PACKET_LEN:
          print '_on_new_connection - Invalid number of bytes to read'
          return

        # Wait until the request data is ready to read
        if not socket.waitForReadyRead(TIMEOUT):
            print 'READ PACKET SIZE : %s' % socket.errorString()
            return

        packet_size = 0
        try:
            # read packet size
            bytes = socket.read(PACKET_LEN)
            (packet_size,) = struct.unpack('L', bytes)
        except:
            raise Exception('READ PACKET SIZE')

        if not socket.waitForReadyRead(TIMEOUT):
            print 'READ REQUEST : %s' % socket.errorString()
            return

        mem_req = []
        try:
            # read the memory request -> [memory key,size]
            bytes = socket.read(packet_size)
            mem_req = pickle.loads(bytes)
        except:
            raise Exception('READ REQUEST')

        try:
            # allocate the shared memory block
            self._create_share_memory( mem_req[0], mem_req[1] )
        except:
            # cancel everything
            self.cancel()

        socket.write('ack')
        if not socket.waitForBytesWritten(TIMEOUT):
            print 'Acknowledge failed: %s\n' % socket.errorString()
            return
        
        del socket

    def _create_share_memory(self, key, size):
        """Create shared memory segment """        
        self.shmem[key] = QtCore.QSharedMemory(key)         
        if not self.shmem[key].create(size):
            print('_create_share_memory error: %s' % self.shmem[key].errorString())
            raise Exception('SHARED MEMORY CREATION ERROR')
        
    def _read_share_memory(self, key):
        """Read shared memory"""
        if not self.shmem[key].isAttached() and not self.shmem[key].attach():
            print('_read_share_memory error: %s' % self.shmem[key].errorString())
            raise Exception('SHARED MEMORY ACCESS ERROR')

        self.shmem[key].lock()
        shdata = None
        try:
            data = self.shmem[key].data()
            shdata = pickle.loads(data.asstring())
        finally:
            self.shmem[key].unlock()
        return shdata
        
    def _on_process_callback( self, sender, notif, arg ):
        """ Called when an event occurs from a process """        
        if notif == Pool.STARTED:
            if self.state == self.STOP:
                self.t1 = time.time()
                self.state = self.RUN
                self.beginCacheLoading.emit()
            return 
                
        elif notif == Pool.ERROR:
            self.state = self.ERROR
            return 
            
        elif notif == Pool.STATE_CHANGE:
            return 
            
        elif notif == Pool.OUTPUT_MSG:
            if self.state == self.ERROR:
                return 
            
            # Process has finished loading the file
            key = bytes.decode( bytes( sender.readAllStandardOutput() ) )
            # read the data from the shared memory block and notify the clients
            try:
                (index, filename, points,colors,sizes) = self._read_share_memory( key )
            except:
                # problem with shared memory, just cancel everything
                self.cancel()
                raise Pool.Error
                
            self.cacheLoaded.emit( index, (filename, points,colors,sizes) )                
            
            # done with the memory block
            self.shmem[key].detach()
            del self.shmem[key]
            
        elif notif == Pool.OUTPUT_ERROR:
            self.state = self.ERROR
            s_out = bytes.decode( bytes( sender.readAllStandardError() ) )
            print 'process error output: %s - %s\nRetry your operation.' % ((repr(sender)),s_out)
            
        elif notif == Pool.FINISHED:
            if self.state == self.STOP:
                return 
            
            if self.state == self.ERROR:
                # tell clients the loading process has been cancelled or was terminated prematurely
                self.cancel()
                return 
                        
            #print 'process finished: %s\n' % (repr(sender))
            self.files_processed += self.file_block
            if self.files_processed >= len(self.files):
                self.t2 = time.time()
                self.state = self.STOP
                self.endCacheLoading.emit()
                print 'Processes %d Loading time %0.3f s' % (self.pool.process_count,self.t2-self.t1)
            return 

class LoaderTask(object):
    """ Task for loading cache files from a process """
    def __init__(self,args):        
        """ 
        Process arguments:
        arg0: list of files
        arg1: list of file indices
        """ 
        self._cmd = 'python.exe loader_process.py "%s" "%s"' % (repr(args[0]),repr(args[1]))

    def __call__(self):
        """ Returns the process command """
        return self._cmd
