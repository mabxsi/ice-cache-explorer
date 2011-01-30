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
from icereader import ICEReader, get_files_from_cache_folder, get_files, is_valid_file
from basics import Vec3
from icereader_util import traceit
from view_tools import ToolManager
from iceloader import ICECacheLoader

import time

# Specify the supported standard ICE attributes
# Note: The PointPosition___ attribute is always required
_supported_attributes_ = ('PointPosition___','Color___')
    
class ICEViewer(QtOpenGL.QGLWidget):
    """ OpenGL viewer for viewing ICE cache data. """
    # PyQt signal slot functions declaration
    
    # arg: cache index, file reader object
    cacheLoaded = QtCore.pyqtSignal(int, object) 
    # args: number of files, start cache, end cache
    beginCacheLoading = QtCore.pyqtSignal(int,int,int)
    endCacheLoading = QtCore.pyqtSignal(int,int,int)
    # arg:cache index, files loading
    beginDrawCache = QtCore.pyqtSignal(int,bool)
    endDrawCache = QtCore.pyqtSignal(int,bool)
    # arg:cache index
    beginPlayback = QtCore.pyqtSignal(int)
    endPlayback = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, x=0, y=0, w=640, h=480):      
        super(ICEViewer, self).__init__(parent)
        
        self.camera = Camera(1., Vec3(20,30,30), Vec3(0,0,0), Vec3(0,1,0))

        # init the animation parameters
        self.cache_count = 0
        self.start_cache = 1
        self.end_cache = 100
        self.current_cache = 1
        self.playback_timerid = -1
        self.playback_time_elapse = 10
        self.load_start_time = 0
        self.play_state = False
        self.loop_state = False
        
        self.point_arrays = {}
        self.color_arrays = {}
        self.size_arrays = {}
        self.statusbar = self.parentWidget().statusBar()
        self.right_msg = parent.right_msg
        self.cache_loading = False

        # view tools management
        self.toolmgr = ToolManager(self)
                
        # Cache loader worker thread
        self.cache_loader_thread = ICECacheLoader()
        self.cache_loader_thread.started.connect( self.on_begin_cacheloading )
        self.cache_loader_thread.cacheLoaded.connect( self.on_cache_loaded )                
        self.cache_loader_thread.finished.connect( self.on_end_cacheloading )

        self.setAcceptDrops( True )                    
        self.setFocusPolicy( QtCore.Qt.StrongFocus )    
    
    def __del__(self):
        self.__stop_playback_timer__( )

    def get_data( self, attribname, cache ):
        """Retrieve the display data"""
        if 'PointPosition___' == attribname and cache in self.point_arrays:
            return self.point_arrays[cache]
        if 'Color___' == attribname and cache in self.color_arrays:
            return self.color_arrays[cache]
        if 'Size' == attribname and cache in self.size_arrays:
            return self.size_arrays[cache]
        return []
             
    def stop_loading(self):
        """ cancel current loading job """
        self.__stop_playback__()
        self.cache_loader_thread.cancel()
        
    def load_files( self, files ):
        """ Load one or multiple cache files. """
        self.point_arrays = {}
        self.color_arrays = {}
        self.size_arrays = {}
        
        (files, startcache, endcache) = get_files( files )
        self.__load_icecache_files__( files, startcache, endcache )        
                    
    def load_files_from_folder(self, dir ):
        """ Load all cache files located in dir """
        self.point_arrays = {}
        self.color_arrays = {}
        self.size_arrays = {}
        
        (files,startcache,endcache) = get_files_from_cache_folder( dir )
        self.__load_icecache_files__( files, startcache, endcache )

    def perspective_view(self):
        """ Set the OGL view as a perspective view. """
        self.toolmgr['PAN' ].panning_vec = Vec3(0,0,0)
        self.camera.set(Vec3(20,30,30), Vec3(0,0,0), Vec3(0,1,0))     
        self._updateGL()
                
    def top_view(self):
        """ Set the OGL view to look through Y axis. """
        self.toolmgr['PAN' ].panning_vec = Vec3(0,0,0)
        self.camera.set(Vec3(0,30,0), Vec3(0,0,0), Vec3(1,0,0))     
        self._updateGL()

    def front_view(self):
        """ Set the OGL view to look through Z axis. """
        self.toolmgr['PAN' ].panning_vec = Vec3(0,0,0)
        self.camera.set(Vec3(0,0,40), Vec3(0,0,0), Vec3(0,1,0))          
        self._updateGL()

    def right_view(self):
        """ Set the OGL view to look through X axis. """
        self.toolmgr['PAN' ].panning_vec = Vec3(0,0,0)
        self.camera.set(Vec3(40,0,0), Vec3(0,0,0), Vec3(0,1,0))            
        self._updateGL()
        
    def left_view(self):
        """ Set the OGL view to look through -X axis. """
        self.toolmgr['PAN' ].panning_vec = Vec3(0,0,0)
        self.camera.set(Vec3(-40,0,0), Vec3(0,0,0), Vec3(0,1,0))            
        self._updateGL()

    def orbit_tool(self):
        """ Activate the orbit tool """
        self.toolmgr.activate_tool( self.toolmgr[ 'ORBIT' ] ) 
        
    def pan_tool(self):
        """ Activate the pan tool """
        self.toolmgr.activate_tool( self.toolmgr[ 'PAN' ] ) 

    def zoom_tool(self):
        """ Activate the zoom tool """
        self.toolmgr.activate_tool( self.toolmgr[ 'ZOOM' ] ) 

    # internals
    def __load_icecache_files__( self, files, startcache, endcache ):
        """ Start worker thread to load icecache files """
        self.cache_count = len(files)
        self.start_cache = startcache
        self.end_cache = endcache
        self.current_cache = startcache
        
        # start loading the file caches
        self.load_start_time = time.clock()
        self.cache_loader_thread.load_cache_files( files, startcache, endcache, _supported_attributes_ )        

    def __start_playback__(self):
        """ Enables a timer to start the playback. The OGL view gets updated when the timer is triggered. """            
        if self.current_cache == self.end_cache:
            self.current_cache = self.start_cache                        
        self.__start_playback_timer__( )

    def __stop_playback__(self):
        """ Stop the playback timer to stop the playback"""
        self.__stop_playback_timer__()
    
    def __start_playback_timer__( self ):
        """ Stop any running playback timer and restart a new playback timer"""
        self.__stop_playback_timer__()
        self.playback_timerid = self.startTimer( self.playback_time_elapse )

    def __stop_playback_timer__(self):
        """ Stop the the playback timer if any """
        try:
            #traceit()
            self.killTimer( self.playback_timerid )
        except:
            pass

    # All signal slots (i.e. callbacks)
    def on_cache_change( self, cache ):
        """ Called when the playback cursor changes """
        self.current_cache = cache
        self._updateGL()

    def on_start_cache_change( self, cache ):
        """ Called when the playback start cache edit box has changed """
        self.start_cache = cache
        self._updateGL()

    def on_end_cache_change( self, cache ):
        """ Called when the playback end cache edit box has changed """
        self.end_cache = cache
        self._updateGL()

    def on_play( self ):
        """ Called when the playback play button is pressed. The callback makes sure the current cache is properly set first and then starts the playback. """
        self.play_state = True
        if self.current_cache >= self.end_cache:            
            # reset to start cache
            self.current_cache = self.start_cache
        self.beginPlayback.emit( self.current_cache )
        self.__start_playback__()

    def on_stop( self ):
        """ Stops the playback when the playback play button is released. """
        self.play_state = False
        self.__stop_playback__()

    def on_loop( self, bFlag ):
        """ Called when the playback loop button is pressed or depressed. """
        self.loop_state = bFlag

    def on_begin_cacheloading(self):
        """ Called by the ICECacheLoader thread at the beginning of the file loading process """
        self.cache_loading = True
        self.beginCacheLoading.emit( self.cache_count, self.start_cache, self.end_cache )

    def on_end_cacheloading(self):
        """ Called by the ICECacheLoader thread at the end of the file loading process """
        self.endCacheLoading.emit( self.cache_count, self.start_cache, self.end_cache )        
        self.cache_loading = False

    def on_cache_loaded(self, cacheindex, data ):
        """ Called by the ICECacheLoader thread for every file loaded """
        self.current_cache = cacheindex
        (reader, points, colors, sizes) = data

        if len(points):
            self.point_arrays[cacheindex] = points
        if len(colors):
            self.color_arrays[cacheindex] = colors
        if len(sizes):
            self.size_arrays[cacheindex] = sizes

        # re-emit to viewer clients
        self.cacheLoaded.emit( cacheindex, reader )        
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
        self.statusbar.clearMessage()
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
                self.statusbar.showMessage( 'Error - Invalid file: %s\n' % f )

        # Performs a basic file extention test just to make sure we have valid files to load
        files_to_load = [ f for f in files if is_valid_file( f ) == True ]
        
        if len(files_to_load):
            self.load_files( files_to_load )
        else:
            self.statusbar.showMessage( 'Error - Invalid file' )
        
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
            self.camera.move( 0.02 )
            self._updateGL()
            return 
            
        if key == QtCore.Qt.Key_Down:
            self.camera.move( -0.02 )
            self._updateGL()
            return
            
        if key == QtCore.Qt.Key_Right:
            self.camera.turn( -0.01, 0, 1, 0 )
            self._updateGL()
            return
            
        if key == QtCore.Qt.Key_Left:
            self.camera.turn( 0.01, 0, 1, 0 )
            self._updateGL()
            return

        # delegate to the tool mananger for handling the current interactive tool
        if self.toolmgr.keyPressEvent( event ):
            self._updateGL()
            return
        
        #delegate to base if we don't consume the key
        super(ICEViewer, self).keyPressEvent(event) 
        
    def mousePressEvent(self, event):       
        """ Handler called when a mouse button is down. We just delegate to the tool mananger for handling the current interactive tool. """
        self.toolmgr.mousePressEvent( event )

    def mouseReleaseEvent(self, event):        
        """ Handler called when a mouse button is up. We just delegate to the tool mananger for handling the current interactive tool. """
        self.toolmgr.mouseReleaseEvent( event )

    def mouseMoveEvent(self, event):        
        """ Handler called when a mouse is moving. We just delegate to the tool mananger for handling the current interactive tool. If the tool is managed then the OGL view is updated."""        
        if self.toolmgr.mouseMoveEvent(event):
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
        self.camera.frustum( w, h )        
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        """ This function draws the particles and the view grid. Signals are sent before and after a frame is drawn. """
        
        # Clear the view  and the depth buffer    
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # always draw the pan tool
        self.toolmgr['PAN' ].draw()
        
        # Update the camera lookup
        self.camera.draw()
        
        # grid
        # todo: use a drawlist
        glPushMatrix()
        glTranslate( 20, 0, 20 )
        glBegin(GL_LINES) 
        glColor3f( .5, .5, .5 )
        for i in range(41):
            glVertex3f(-40, 0, -40 + i)
            glVertex3f( 0, 0, -40 + i)
            glVertex3f(-40 + i, 0, -40 )
            glVertex3f(-40 + i, 0,  0 )
        glEnd()
        glPopMatrix()
        
        # coord system
        # todo: use a drawlist
        glPushMatrix()
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

        self.beginDrawCache.emit( self.current_cache, self.cache_loading )

        if self.cache_count and self.current_cache in self.point_arrays and len(self.point_arrays[ self.current_cache ]) > 0:
            # Draw the particles for the current cache (i.e. frame)
            glPushMatrix()

            # use fixed point size for now
            # todo: we should use a GLSL shader to render the particle sizes
            glPointSize( 2.0 )

            glEnableClientState(GL_VERTEX_ARRAY)
            if self.current_cache in self.color_arrays:
                glEnableClientState(GL_COLOR_ARRAY);          
            else:
                # default color
                # todo: should be optional
                glColor3f( 0.0, 0.7, 0.0 )

            glVertexPointerd(self.point_arrays[ self.current_cache ])            
            if self.current_cache in self.color_arrays:
                glColorPointerd(self.color_arrays[ self.current_cache ])
            
            glDrawArrays(GL_POINTS, 0, len(self.point_arrays[ self.current_cache ]))
            
            glDisableClientState(GL_VERTEX_ARRAY)
            
            if self.current_cache in self.color_arrays:
                glDisableClientState(GL_COLOR_ARRAY)

            glPopMatrix()

        self.endDrawCache.emit( self.current_cache, self.cache_loading )

    def timerEvent( self, event ):
        """ render the current cache """                

        if self.current_cache == self.end_cache:
            # end of frames
            self.endPlayback.emit( self.current_cache )

            if self.loop_state == False:
                # stop playback
                self.__stop_playback__()
                return
            else:
                # reset to start cache
                self.current_cache = self.start_cache

        if self.current_cache != self.end_cache:
            self.current_cache += 1
            
        self._updateGL()
        
    def _updateGL( self ):
        """ update the OGL view """
        #traceit()
        self.updateGL()

def test():
    viewer = ICEViewerOGL(0,0,640,480)    
    
    dir = r'C:\dev\icecache_data\cache6'

    #viewer.log_info( dir )
    viewer.start( dir )

    glutMainLoop()      

if __name__=='__main__':
    test()
		
