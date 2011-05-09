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

from math import pi
from math import cos
from math import sin
from OpenGL import GL, GLU, GLUT
from basics import Vec3

class Camera( object ):
    def __init__( self, fov, origin, focus, up ):
        self.fov = fov
        self.set( origin, focus, up )

    def set( self, origin, focus, up ):
        self.focus = Vec3(focus.x, focus.y, focus.z )
        self.origin = Vec3(origin.x, origin.y, origin.z )
        self.up	= Vec3(up.x, up.y, up.z)

    def frustum( self, w, h ):
        """Set up the viewing Frustum"""
        if w and h:
            aspect = float(w)/float(h)
        else:
            aspect = 1.0
        GLU.gluPerspective(self.fov * 180.0 / pi, aspect, 0.001, 1000.0)

    def ortho2D( self, w, h ):
        GLU.gluOrtho2D(0, w/2, h/2, 0);        

    def draw(self):
        GLU.gluLookAt( self.origin.x, self.origin.y, self.origin.z, self.focus.x, self.focus.y, self.focus.z, self.up.x, self.up.y, self.up.z )  
        
    def move( self, rate):
        v = Vec3()
        v = self.focus - self.origin

        self.origin.y += v.y * rate
        self.focus.y += v.y * rate
        self.origin.x += v.x * rate 
        self.origin.z += v.z * rate 
        self.focus.x += v.x * rate
        self.focus.z += v.z * rate 

    def move_from_mouse(self,mousex,mousey):
                                
        centerx = glutGet( GLUT_WINDOW_WIDTH ) >> 1
        centery = glutGet( GLUT_WINDOW_HEIGHT ) >> 1  
        
        yAngle = 0
        zAngle = 0  
        totalRot = 0  
        lastRot = 0  
      
        if mousex == centerx and self.mousey == centery:
            return  
       
        #SetCursorPos(centerx, centery)  
      
        yAngle = (float)(centerx - mousex)/1000  
        zAngle = (float)(centery - mousey)/1000  
        
        lastRot = totalRot  
        totalRot += zAngle  
        
        """
        Here we check if we have gone over the boundry. In our case, 1.0f is the acting boundry, 
        you can play around with this value, but if you place it too low, the camera will flip. 
        Too high and your degree of motion is severly limited. You have to find a soft middle. 
        """  
        if totalRot > 1:  
            totalRot = 1  
        
            if lastRot != 1:  
                axis = self.focus - self.origin
                axis.cross( self.up )  
                axis.normalize()  
                self.turn(1.0 - lastRot, axis.x, axis.y, axis.z)  
         
        elif totalRot < -1:  
            totalRot = -1  
            
            if lastRot != -1:
                axis = self.focus - self.origin
                axis.cross( self.up )  
                axis.normalize()  
                self.turn(1.0 - lastRot, axis.x, axis.y, axis.z)  
          
        else:
            """
            Here, we don't have to check any boundries. IT is obvious that they did not  
            hit 1 if it reaches this point. We just turn normally in this case. 
            """ 
            axis = self.focus - self.origin
            axis.cross( self.up )  
            axis.normalize()  
            self.turn(zAngle, axis.x, axis.y, axis.z)  
        
        """
        We ALWAYS turn left or right. No boundries are needed since the camera will not flip.  
        """
        self.turn( yAngle, 0, 1, 0 )
        
        
    def turn(self, angle, x, y, z):      
        fView = self.focus - self.origin
        
        cosTheta = cos(angle)  
        sinTheta = sin(angle)
        
        newFocus = Vec3()  
        
        newFocus.x  = (cosTheta + (1 - cosTheta) * x * x) * fView.x
        newFocus.x += ((1 - cosTheta) * x * y - z * sinTheta) * fView.y
        newFocus.x += ((1 - cosTheta) * x * z + y * sinTheta) * fView.z  
        
        newFocus.y  = ((1 - cosTheta) * x * y + z * sinTheta) * fView.x  
        newFocus.y += (cosTheta + (1 - cosTheta) * y * y) * fView.y  
        newFocus.y += ((1 - cosTheta) * y * z - x * sinTheta) * fView.z  
         
        newFocus.z  = ((1 - cosTheta) * x * z - y * sinTheta) * fView.x  
        newFocus.z += ((1 - cosTheta) * y * z + x * sinTheta) * fView.y  
        newFocus.z += (cosTheta + (1 - cosTheta) * z * z) * fView.z  
        
        self.focus = self.origin + newFocus  

    