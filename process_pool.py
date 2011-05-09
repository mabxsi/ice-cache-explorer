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
import sys
import time

from Queue import Queue, Empty

class Pool(QtCore.QObject):
    """ Class representing a process pool """
    
    # process states
    STARTED = 0
    ERROR = 1
    STATE_CHANGE = 2
    OUTPUT_MSG = 3
    OUTPUT_ERROR_MSG = 4
    FINISHED = 5
    
    # callback exception
    class Error(Exception):
        pass
    
    def __init__( self, parent ):
        super(Pool,self).__init__(parent)
        self._callback  = None
        self._all_processes = None
        self._in_processes = None
        self._tasks = None
        self._proc_count = 1
        self._callback = None
        self._serving = False

    def init( self, process_count=1, callback=None ):    
        self._kill_all_processes()                
        self._proc_count = process_count
        if callback != None:
            self._callback = callback
        self._tasks = Queue()
        self._in_processes = Queue()
        self._all_processes = Queue()
        self._serving = False
        self._populate_pool()

    def submit( self, task ):        
        self._tasks.put( task )
        self._process_tasks()
    
    def cancel(self):
        self._kill_all_processes()
        #self._populate_pool()
                        
    @property
    def process_count(self):
        return self._proc_count
        
    def _populate_pool(self):
        for i in range(self._proc_count-self._in_processes.qsize()):
            p = QtCore.QProcess(self.parent())
            self._in_processes.put( p )
            self._all_processes.put( p )
            # setup notif callbacks
            p.started.connect(self._on_process_started)
            p.error.connect( self._on_process_error )
            p.readyReadStandardOutput.connect( self._on_process_output )
            p.readyReadStandardError.connect( self._on_process_error_output )
            p.stateChanged.connect(self._on_process_state_change)                   
            p.finished.connect(self._on_process_finished)        

    def _process_tasks(self): 
        if self._serving:
            return        
        self._serving = True

        while not self._in_processes.empty():            
            if self._tasks.empty():
                self._serving = False
                return
            
            p = self._in_processes.get()
            t = self._tasks.get()
            try:
                # try with callable object 
                p.start( t() )            
            except:
                try:
                    # try with string type                    
                    p.start( t )
                except:
                    raise
        
        self._serving = False

    def _kill_all_processes(self):        
        """ stop pending processes """
        try:
            while not self._all_processes.empty():
                p = self._all_processes.get()
                try:
                    p.close()
                except:
                    print sys.exc_info()
        except:
            pass            

        try:
            while 1:
                self._in_processes.get_nowait()
        except:
            pass            

        try:
            while 1:
                self._tasks.get_nowait()
        except:
            pass            
            
    def _on_process_started( self ):
        try:
            #print 'process started: %d' % self.sender().pid()
            if self._callback != None:            
                self._callback( self.sender(), self.STARTED, None )
        except:
             print '_on_process_started error: %s' % sys.exc_info()[1]
     
    def _on_process_error(self,error):
        errors = ["Failed to start", "Crashed", "Timedout", "Read error", "Write Error", "Unknown Error"]        
        try:
            #print 'process error: %d - %s' % (self.sender().pid(), errors[error])
            if self._callback != None:            
                self._callback( self.sender(), self.ERROR, errors[error] )
        except:
             print '_on_process_error error: %s' % sys.exc_info()[1]
             
    def _on_process_state_change(self,new_state):
        states = ["Not running", "Starting", "Running"]
        try:
            #print 'process in new state: %d - %s' % (self.sender().pid(), states[new_state])
            if self._callback != None:
                self._callback( self.sender(), self.STATE_CHANGE, states[new_state] )
        except:
             print '_on_process_state_change error: %s' % sys.exc_info()[1]
             
    def _on_process_output(self):
        try:
            if self._callback != None:            
                self._callback( self.sender(), self.OUTPUT_MSG, None )
        except Pool.Error:
            self.cancel()
        
    def _on_process_error_output(self):
        try:            
            if self._callback != None:            
                self._callback( self.sender(), self.OUTPUT_ERROR_MSG, None )
        except:
            print '_on_process_error_output error: %s' % sys.exc_info()[1]

    def _on_process_finished(self):
        #print 'process finished: %s' % (str(self.sender()))
        if self._callback != None:            
            self._callback( self.sender(), self.FINISHED, None )
        
        # put process back in the pool
        self._in_processes.put( self.sender() )
        # process other tasks if any
        self._process_tasks( )
        
if __name__ == '__main__':
    import multiprocessing as mp
    pool = Pool( )
    pool.init( mp.cpu_count )
    
    pool.submit( 'python test.py "toto"' )
    pool.submit( 'python test.py "toto2"' )
    pool.submit( 'python test.py "toto3"' )
    