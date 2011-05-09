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

import sys
import re
import os

try:
    from PyQt4 import QtCore, QtGui, QtOpenGL
except:
    print "ERROR: PyQt4 not installed properly."
    sys.exit()

try: 
    import OpenGL
    # to report data array copy as errors
    OpenGL.ERROR_ON_COPY = True

    from OpenGL.GLUT import *
    from OpenGL.GL import *
    from OpenGL.GLU import *
except:
    print "ERROR: PyOpenGL not installed properly."
    sys.exit()

try:
    import numpy 
except:
    print "ERROR: numpy not installed properly."
    sys.exit()

from camera import Camera
import icereader as icer 
import h5reader as h5r 
from basics import Vec3
from icereader_util import traceit, get_files_from_cache_folder, get_files
from view_tools import ToolManager
from iceloader import ICECacheLoader

import time

class ICEViewer(QtOpenGL.QGLWidget):
    """ OpenGL viewer for viewing ICE cache data. """
    # PyQt signal slot functions declaration
    
    # arg: cache index, file reader object
    #cacheLoaded = QtCore.pyqtSignal(int, object) 
    cacheLoaded = QtCore.pyqtSignal(int, str) 
    # args: number of files, start cache, end cache
    beginCacheLoading = QtCore.pyqtSignal(int,int,int)
    endCacheLoading = QtCore.pyqtSignal(int,int,int)
    # arg:cache index, files loading
    beginDrawCache = QtCore.pyqtSignal(int,bool)
    endDrawCache = QtCore.pyqtSignal(int,bool)
    # arg:cache index
    beginPlayback = QtCore.pyqtSignal(int)
    endPlayback = QtCore.pyqtSignal(int)

    GRID_SIZE = 40
    
    def __init__(self, parent=None, x=0, y=0, w=640, h=480):      
        super(ICEViewer, self).__init__(parent)
        
        self._camera = Camera(1., Vec3(20,30,30), Vec3(0,0,0), Vec3(0,1,0))

        # init the animation parameters
        self._cache_count = 0
        self._start_cache = 1
        self._end_cache = 100
        self._current_cache = 1
        self._playback_timerid = -1
        self._playback_time_elapse = 10
        self._load_start_time = 0
        self._play_state = False
        self._loop_state = False
        
        self._statusbar = self.parentWidget().statusBar()
        self._right_msg = parent.right_msg
        self._cache_loading = False

        # view tools management
        self._toolmgr = ToolManager(self)
                
        # Cache loader object
        self._cache_loader = ICECacheLoader(parent)
        self._cache_loader.beginCacheLoading.connect( self.on_begin_cacheloading )
        self._cache_loader.cacheLoaded.connect( self.on_cache_loaded )                
        self._cache_loader.endCacheLoading.connect( self.on_end_cacheloading )

        self.setAcceptDrops( True )                    
        self.setFocusPolicy( QtCore.Qt.StrongFocus )    

        self._create_grid_data( self.GRID_SIZE )

    def __del__(self):
        self._stop_playback_timer( )

    @property
    def cache(self):
        return self._cache_loader

    @property
    def camera(self):
        return self._camera

    @property
    def right_msg(self):
        return self._right_msg
        
    def stop_loading(self):
        """ cancel current loading job """
        self.__stop_playback__()
        self._cache_loader.cancel()
        
    def load_files( self, files ):
        """ Load one or multiple cache files. """        
        (files, startcache, endcache) = get_files( files )
        self._load_icecache_files( files, startcache, endcache )        
                    
    def load_files_from_folder(self, dir ):
        """ Load all cache files located in dir """        
        (files,startcache,endcache) = get_files_from_cache_folder( dir )
        self._load_icecache_files( files, startcache, endcache )

    def perspective_view(self): 
        """ Set the OGL view as a perspective view. """
        self._toolmgr['PAN' ].panning_vec = Vec3(0,0,0)
        self._camera.set(Vec3(20,30,30), Vec3(0,0,0), Vec3(0,1,0))     
        self._updateGL()
                
    def top_view(self):
        """ Set the OGL view to look through Y axis. """
        self._toolmgr['PAN' ].panning_vec = Vec3(0,0,0)
        self._camera.set(Vec3(0,30,0), Vec3(0,0,0), Vec3(1,0,0))     
        self._updateGL()

    def front_view(self):
        """ Set the OGL view to look through Z axis. """
        self._toolmgr['PAN' ].panning_vec = Vec3(0,0,0)
        self._camera.set(Vec3(0,0,40), Vec3(0,0,0), Vec3(0,1,0))          
        self._updateGL()

    def right_view(self):
        """ Set the OGL view to look through X axis. """
        self._toolmgr['PAN' ].panning_vec = Vec3(0,0,0)
        self._camera.set(Vec3(40,0,0), Vec3(0,0,0), Vec3(0,1,0))            
        self._updateGL()
        
    def left_view(self):
        """ Set the OGL view to look through -X axis. """
        self._toolmgr['PAN' ].panning_vec = Vec3(0,0,0)
        self._camera.set(Vec3(-40,0,0), Vec3(0,0,0), Vec3(0,1,0))            
        self._updateGL()

    def orbit_tool(self):
        """ Activate the orbit tool """
        self._toolmgr.activate_tool( self._toolmgr[ 'ORBIT' ] ) 
        
    def pan_tool(self):
        """ Activate the pan tool """
        self._toolmgr.activate_tool( self._toolmgr[ 'PAN' ] ) 

    def zoom_tool(self):
        """ Activate the zoom tool """
        self._toolmgr.activate_tool( self._toolmgr[ 'ZOOM' ] ) 

    # internals
    def _load_icecache_files( self, files, startcache, endcache ):
        """ Start worker thread to load icecache files """
        self._cache_count = len(files)
        self._start_cache = startcache
        self._end_cache = endcache
        self._current_cache = startcache
        
        # start loading the file caches
        self._load_start_time = time.clock()
        self._cache_loader.load_cache_files( files, startcache, endcache )        

    def __start_playback__(self):
        """ Enables a timer to start the playback. The OGL view gets updated when the timer is triggered. """            
        if self._current_cache == self._end_cache:
            self._current_cache = self._start_cache                        
        self.__start_playback_timer__( )

    def __stop_playback__(self):
        """ Stop the playback timer to stop the playback"""
        self._stop_playback_timer()
    
    def __start_playback_timer__( self ):
        """ Stop any running playback timer and restart a new playback timer"""
        self._stop_playback_timer()
        self._playback_timerid = self.startTimer( self._playback_time_elapse )

    def _stop_playback_timer(self):
        """ Stop the the playback timer if any """
        try:
            #traceit()
            self.killTimer( self._playback_timerid )
        except:
            pass

    # All signal slots (i.e. callbacks)
    def on_cache_change( self, cache ):
        """ Called when the playback cursor changes """
        self._current_cache = cache
        self._updateGL()

    def on_start_cache_change( self, cache ):
        """ Called when the playback start cache edit box has changed """
        self._start_cache = cache
        self._updateGL()

    def on_end_cache_change( self, cache ):
        """ Called when the playback end cache edit box has changed """
        self._end_cache = cache
        self._updateGL()

    def on_play( self ):
        """ Called when the playback play button is pressed. The callback makes sure the current cache is properly set first and then starts the playback. """
        self._play_state = True
        if self._current_cache >= self._end_cache:            
            # reset to start cache
            self._current_cache = self._start_cache
        self.beginPlayback.emit( self._current_cache )
        self.__start_playback__()

    def on_stop( self ):
        """ Stops the playback when the playback play button is released. """
        self._play_state = False
        self.__stop_playback__()

    def on_loop( self, bFlag ):
        """ Called when the playback loop button is pressed or depressed. """
        self._loop_state = bFlag

    def on_begin_cacheloading(self):
        """ Called by the ICECacheLoader object at the beginning of the file loading process """
        self._cache_loading = True
        self.beginCacheLoading.emit( self._cache_count, self._start_cache, self._end_cache )

    def on_end_cacheloading(self):
        """ Called by the ICECacheLoader object at the end of the file loading process """
        self.endCacheLoading.emit( self._cache_count, self._start_cache, self._end_cache )        
        self._cache_loading = False

    def on_cache_loaded(self, cacheindex, filename ):
        """ Called by the ICECacheLoader object for every file loaded """
        self._current_cache = cacheindex
        # re-emit to viewer clients
        self.cacheLoaded.emit( cacheindex, filename )        
        self._updateGL()

    # widget callbacks
    def dragEnterEvent(self, e):
        """ Accept DnD event for files only """
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore() 

    def dropEvent(self, e):
        """ Load valid icecache files from event """
        self._statusbar.clearMessage()
        files = []
        for url in e.mimeData().urls():
            f = url.toLocalFile()
            
            if os.path.isfile( f ):                
                files.append( f )            
            elif os.path.isdir( f ):
                t = get_files_from_cache_folder( f )
                if t != ():
                    (files,st,end) = t
                break
            else: 
                self._statusbar.showMessage( 'Error - Invalid file: %s\n' % f )

        # Performs a basic file extention test just to make sure we have valid files to load
        files_to_load = [ f for f in files if is_valid_file( f ) == True ]
        
        if len(files_to_load):
            self.load_files( files_to_load )
        else:
            self._statusbar.showMessage( 'Error - Invalid file' )
        
    def keyPressEvent( self, event ):
        """ Keyboard handler """
        key = event.key()
                                
        if key == QtCore.Qt.Key_F1:
            self.perspective_view()
            return
            
        if key == QtCore.Qt.Key_F2:
            self.top_view()
            return
            
        if key == QtCore.Qt.Key_F3:
            self.front_view()
            return
            
        if key == QtCore.Qt.Key_F4:
            self.left_view()            
            return 
            
        if key == QtCore.Qt.Key_F5:
            self.right_view()
            return
            
        if key == QtCore.Qt.Key_Up:
            self._camera.move( 0.02 )
            self._updateGL()
            return 
            
        if key == QtCore.Qt.Key_Down:
            self._camera.move( -0.02 )
            self._updateGL()
            return
            
        if key == QtCore.Qt.Key_Right:
            self._camera.turn( -0.01, 0, 1, 0 )
            self._updateGL()
            return
            
        if key == QtCore.Qt.Key_Left:
            self._camera.turn( 0.01, 0, 1, 0 )
            self._updateGL()
            return

        # delegate to the tool mananger for handling the current interactive tool
        if self._toolmgr.keyPressEvent( event ):
            self._updateGL()
            return
        
        #delegate to base if we don't consume the key
        super(ICEViewer, self).keyPressEvent(event) 
        
    def mousePressEvent(self, event):       
        """ Handler called when a mouse button is down. We just delegate to the tool mananger for handling the current interactive tool. """
        self._toolmgr.mousePressEvent( event )

    def mouseReleaseEvent(self, event):        
        """ Handler called when a mouse button is up. We just delegate to the tool mananger for handling the current interactive tool. """
        self._toolmgr.mouseReleaseEvent( event )

    def mouseMoveEvent(self, event):        
        """ Handler called when a mouse is moving. We just delegate to the tool mananger for handling the current interactive tool. If the tool is managed then the OGL view is updated."""        
        if self._toolmgr.mouseMoveEvent(event):
            self._updateGL()
                    
    def initializeGL(self):
        """ Initialized the OGL view """
        glClearColor(0.2, 0.2, 0.2, 0.0)
        glClearDepth(1.0)
        glDepthFunc(GL_LESS)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)	
        
    def minimumSizeHint(self):
        """ OGL view minimum size """
        return QtCore.QSize(50, 50)

    def sizeHint(self):
        """ OGL view maximum size """
        return QtCore.QSize(640, 400)
               
    def resizeGL(self, w, h):
        """ Called when the OGL view is being resized. The function makes sure the viewport and the camera frustrum are updated accordingly."""
        side = min(w, h)
        if side < 0:
            return
    
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        self._camera.frustum( w, h )        
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        """ This function draws the particles and the view grid. Signals are sent before and after a frame is drawn. """
        
        # Clear the view  and the depth buffer    
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # always draw the pan tool
        self._toolmgr['PAN' ].draw()
        
        # Update the camera lookup
        self._camera.draw()
        
        # grid        
        glLineWidth(1.0)
        glEnableClientState(GL_VERTEX_ARRAY)        
        glPushMatrix()
        glTranslate( self.GRID_SIZE/2, 0, self.GRID_SIZE/2 )
        glColor3f( .5, .5, .5 )
        glVertexPointerf( self.grid_array )
        glDrawArrays(GL_LINES, 0, len(self.grid_array))
        glPopMatrix()
        glDisableClientState(GL_VERTEX_ARRAY)
        
        # coord system
        # todo: use a drawlist
        glPushMatrix()
        glLineWidth(2.0)
        glBegin(GL_LINES) 
        glColor3f( 1.0, 0.0, 0.0 )
        glVertex3f(0, 0, 0)
        glVertex3f(1, 0, 0)

        glColor3f( 0.0, 1.0, 0.0 )
        glVertex3f(0, 0, 0)
        glVertex3f(0, 1, 0)

        glColor3f( 0.0, 0.0, 1.0 )
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 1)
        glEnd()
        glPopMatrix()

        self.beginDrawCache.emit( self._current_cache, self._cache_loading )
                
        points = self._cache_loader.points( self._current_cache )            
        num_points = len(points)
        if num_points:
            # Draw the particles for the current cache (i.e. frame)
            glPushMatrix()

            # use fixed point size for now
            # todo: we should use a GLSL shader to render the particle sizes
            glPointSize( 2.0 )

            glEnableClientState(GL_COLOR_ARRAY)            
            try:
                colors = self._cache_loader.colors( self._current_cache )
                glColorPointerf(colors)
            except:
                # default color
                # todo: should be optional
                glColor3f( 0.0, 0.7, 0.0 )

            glEnableClientState(GL_VERTEX_ARRAY)                
            glVertexPointerf( points )                                                                
            glDrawArrays(GL_POINTS, 0, num_points )            
            glDisableClientState(GL_VERTEX_ARRAY)

            glDisableClientState(GL_COLOR_ARRAY)
            
            glPopMatrix()

        self.endDrawCache.emit( self._current_cache, self._cache_loading )

    def _create_grid_data(self, size ):
        self.grid_array = numpy.zeros( ((size+1)*4,3), numpy.float32 )
        
        for i in range( size+1 ):
            self.grid_array[i*4+0] = [-size, 0, -size + i]
            self.grid_array[i*4+1] = [0, 0, -size + i]
            self.grid_array[i*4+2] = [-size + i, 0, -size]
            self.grid_array[i*4+3] = [-size + i, 0, 0]

    def timerEvent( self, event ):
        """ render the current cache """                

        if self._current_cache == self._end_cache:
            # end of frames
            self.endPlayback.emit( self._current_cache )

            if self._loop_state == False:
                # stop playback
                self.__stop_playback__()
                return
            else:
                # reset to start cache
                self._current_cache = self._start_cache

        if self._current_cache != self._end_cache:
            self._current_cache += 1
            
        self._updateGL()
        
    def _updateGL( self ):
        """ update the OGL view """
        #traceit()
        self.updateGL()

def is_valid_file( f ):
    return icer.is_valid_file(f) or h5r.is_valid_file(f)

def test():
    pass
    
if __name__=='__main__':
    test()
		
