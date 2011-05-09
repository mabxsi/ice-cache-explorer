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

from PyQt4 import QtCore
import time
import sys
import os
from process_pool import Pool
import h5py as h5

POINT_DATA = '/ATTRIBS/PointPosition___/Data'
COLOR_DATA = '/ATTRIBS/Color___/Data'
SIZE_DATA = '/ATTRIBS/Size/Data'

class ICECacheLoader(QtCore.QObject):
    """ Class for loading cache files. Files are loaded through processes managed by the Pool class. The data loaded
    by processes is sent to ICECacheLoader via PyQt's QLocalSocket and QLocalServer which are basically a named pipe. """
    # signal sent for each new loaded cache
    # int: cache index
    # tuple: (reader, points, colors, sizes)
    #cacheLoaded = QtCore.pyqtSignal( int, tuple ) 
    cacheLoaded = QtCore.pyqtSignal( int, str ) 
    beginCacheLoading = QtCore.pyqtSignal()
    endCacheLoading = QtCore.pyqtSignal()

    # Loading state
    STOP = 0
    RUN = 1
    ERROR = 2
    
    def __init__(self, parent = None):    
        super(ICECacheLoader,self).__init__(parent)
        self._pool = None
        self._state = self.STOP
        self._files = []
        self._cache = {}
        
    def init_process_server( self ):
        self._state = self.STOP
        self._files = []
        self._cache = {}
        self._pool = Pool(self)
        self._pool.init(self.parent().prefs.process_count, self._on_process_callback)

    def cancel(self):
        self._state = self.STOP
        self.endCacheLoading.emit()        
        if self._pool:
            self._pool.cancel()
        print "Operation was cancelled."

    def points( self, cache_index ):            
        if cache_index in self._cache and self._cache[ cache_index ] != None and POINT_DATA in self._cache[ cache_index ]:
            return self._cache[ cache_index ][ POINT_DATA ][:]
        return []

    def colors( self, cache_index ):
        if cache_index in self._cache and self._cache[ cache_index ] != None and COLOR_DATA in self._cache[ cache_index ]:
            return self._cache[ cache_index ][ COLOR_DATA ][:]
        return []
            
    def sizes( self, cache_index ):
        if cache_index in self._cache and self._cache[ cache_index ] != None and SIZE_DATA in self._cache[ cache_index ]:
            return self._cache[ cache_index ][ SIZE_DATA ][:]
        return []            

    def __getitem__( self, arg ):
        """ return item cache by index """
        return self._cache[ arg ]
    
    def load_cache_files( self, files, start, end ):    
        """ Start the loading process. """         
        # initialize the process server first
        self.init_process_server()

        self._files = files
        self.startindex = start
        self.endindex = end        

        # file_block can be used to assing multiple files per process. 
        # note: Normally this would make poor load-balancing and affect performance load
        self.file_block = 1
        self.indexset = range(0,len(self._files),self.file_block)     

        # Submit all load tasks to the process pool
        # note: 1 file / task gives very good performance in general.
        self._state = self.STOP
        file_count = len(self._files)
        self._files_processed = 0
        index = self.startindex
        for i in self.indexset:
            file_list = []
            file_index = []
            for j in range(self.file_block):
                if i+j < file_count:
                    file_list.append( self._files[i+j] )
                    file_index.append( index )
                    index += 1                    
            self._pool.submit( LoaderTask( [ file_list, file_index ] ) )
        
    def _on_process_callback( self, sender, notif, arg ):
        """ Called when an event occurs from a process """        
        if notif == Pool.STARTED:
            if self._state == self.STOP:
                self.t1 = time.time()
                self._state = self.RUN
                self.beginCacheLoading.emit()
            return 
                
        elif notif == Pool.ERROR:
            self._state = self.ERROR
            return 
            
        elif notif == Pool.STATE_CHANGE:
            return 
            
        elif notif == Pool.OUTPUT_MSG:
            if self._state == self.ERROR:
                return 
            # Process has finished loading the file
            s_data = bytes.decode( bytes( sender.readAllStandardOutput() ) )
            try:
                data = eval(s_data) 
                # save cache
                self._cache[ data[0] ] = h5.File( data[1], 'r' )
                
                # notify clients                
                self.cacheLoaded.emit( data[0], data[1] )
                
            except:
                # problem, just cancel everything
                self.cancel()
                raise Pool.Error
                         
        elif notif == Pool.OUTPUT_ERROR_MSG:
            self._state = self.ERROR
            s_out = bytes.decode( bytes( sender.readAllStandardError() ) )
            print 'process error output: %s - %s\nRetry your operation.' % ((repr(sender)),s_out)
            
        elif notif == Pool.FINISHED:
            if self._state == self.STOP:
                return 
            
            if self._state == self.ERROR:
                # tell clients the loading process has been cancelled or was terminated prematurely
                self.cancel()
                return 
                        
            #print 'process finished: %s\n' % (repr(sender))
            self._files_processed += self.file_block
            if self._files_processed >= len(self._files):
                self.t2 = time.time()
                self._state = self.STOP
                self.endCacheLoading.emit()
                print 'Processes %d Loading time %0.3f s' % (self._pool.process_count,self.t2-self.t1)
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
