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
from PyQt4 import QtCore, QtGui
from OpenGL.GL import *
from basics import Vec3
from icereader_util import report_error

class ViewTool(object):    
    def __init__(self, name, parent):
        self.name = name
        self.parent = parent
        self.active = False
        self.key = -1

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False        

    def move(self, mouse_button, deltaX, deltaY ):
        return False
    
    def draw(self):
        pass
    
class NoTool(ViewTool):
    def __init__(self,parent):
        super(NoTool,self).__init__( 'NOTOOL', parent )
        self.key = QtCore.Qt.Key_Escape

    def activate(self):
        super(NoTool,self).activate()
        self.parent.right_msg.setText("")            
        
class PanTool(ViewTool):
    def __init__(self,parent):
        super(PanTool,self).__init__( 'PAN', parent )
        self.panning_vec = Vec3()
        self.key = QtCore.Qt.Key_P
        self.cursor = QtGui.QCursor( QtGui.QPixmap( './resources/pan_cursor.png' ) )
            
    def activate(self):
        super(PanTool,self).activate()        
        self.parent.setCursor( self.cursor )
        self.parent.right_msg.setText("PAN: Left Mouse Button, ZOOM: Right Mouse Button")            

    def move(self, mouse_button, deltaX, deltaY ):
        if mouse_button == QtCore.Qt.LeftButton:
            factor = 0.02
            self.panning_vec.x += deltaX * factor
            self.panning_vec.y -= deltaY * factor
            return True
        elif mouse_button == QtCore.Qt.RightButton:
            if deltaY > 0:
                self.parent.camera.move( -0.01 )
            else:
                self.parent.camera.move( 0.01 )
            return True
            
        return False
    
    def draw( self ):
        glTranslate( self.panning_vec.x, self.panning_vec.y, self.panning_vec.z )

class OrbitTool(ViewTool):
    def __init__(self,parent):
        super(OrbitTool,self).__init__( 'ORBIT', parent )
        self.key = QtCore.Qt.Key_O
        self.cursor = QtGui.QCursor( QtGui.QPixmap( './resources/orbit_cursor.png' ) )
        
    def activate(self):
        super(OrbitTool,self).activate()
        self.parent.setCursor( self.cursor )
        self.parent.right_msg.setText("ORBIT: Left Mouse Button, ZOOM: Right Mouse Button")            

    def move(self, mouse_button, deltaX, deltaY ):
        if mouse_button == QtCore.Qt.LeftButton:
            factor = 0.02
            self.parent.camera.origin.x -= deltaX * factor
            self.parent.camera.origin.y += deltaY * factor
            return True
        elif mouse_button == QtCore.Qt.RightButton:
            if deltaY > 0:
                self.parent.camera.move( -0.01 )
            else:
                self.parent.camera.move( 0.01 )
            return True
            
        return False

class ZoomTool(ViewTool):
    def __init__(self,parent):
        super(ZoomTool,self).__init__( 'ZOOM', parent )
        self.key = QtCore.Qt.Key_Z
        self.cursor = QtGui.QCursor( QtGui.QPixmap( './resources/zoom_cursor.png' ) )

    def activate(self):
        super(ZoomTool,self).activate()
        self.parent.setCursor( self.cursor )
        self.parent.right_msg.setText("ZOOM: Left/Right Mouse Button")            

    def move(self, mouse_button, deltaX, deltaY ):
        if mouse_button == QtCore.Qt.LeftButton or mouse_button == QtCore.Qt.RightButton:
            if deltaY > 0:
                self.parent.camera.move( -0.01 )
            else:
                self.parent.camera.move( 0.01 )
            return True
            
        return False

class ToolManager(object):    
    def __init__(self,parent):
        self.mouse_button = QtCore.Qt.NoButton
        self.old_mousex = 0
        self.old_mousey = 0                       
        
        self.tools_from_name = {}
        self.tools_from_key = {}
        
        self.old_cursor = parent.cursor()
        
        tool = PanTool( parent )        
        self.tools_from_name[ tool.name ] = tool
        self.tools_from_key[ tool.key ] = tool

        tool = ZoomTool( parent )        
        self.tools_from_name[ tool.name ] = tool
        self.tools_from_key[ tool.key ] = tool

        tool = OrbitTool( parent )        
        self.tools_from_name[ tool.name ] = tool
        self.tools_from_key[ tool.key ] = tool

        tool = NoTool( parent )        
        self.tools_from_name[ tool.name ] = tool
        self.tools_from_key[ tool.key ] = tool

        # start with the 'no tool'
        self.active_tool = self.tools_from_name[ 'NOTOOL' ]

    def mousePressEvent(self, event):       
        self.mouse_button = event.button()
        self.old_mousex, self.old_mousey = event.x(), event.y()        

    def mouseReleaseEvent(self, event):        
        self.mouse_button = QtCore.Qt.NoButton        
        self.old_mousex, self.old_mousey = event.x(), event.y()        

    def mouseMoveEvent(self, event):        
        x = event.x()
        y = event.y()

        deltaX = x - self.old_mousex
        deltaY = y - self.old_mousey

        if self.active_tool.move( self.mouse_button, deltaX, deltaY ):
            self.old_mousex, self.old_mousey = x, y
            return True
        return False

    def keyPressEvent( self, event ):
        try:            
            self.activate_tool( self.tools_from_key[ event.key() ] )
            return True
        except:
            pass
        return False

    def activate_tool( self, tool ):
        # deactivate current 
        try:
            tool.deactivate()
            tool.parent.setCursor( self.old_cursor )
        except:
            report_error( 'tool error %s' % tool.name )

        #activate new tool
        self.active_tool = tool
        self.old_cursor = tool.parent.cursor()
        tool.activate()
            
    def __getitem__( self, name ):
        return self.tools_from_name[ name ]
       