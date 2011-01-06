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

import types, math
EPS = 1E-12

class Vec3:    
    def __init__(self,x=0.0,y=0.0,z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return 'Vec3('+`self.x`+', '+`self.y`+', '+`self.z`+')'

    def __str__(self):
        fmt="%1.4f"
        return '('+fmt%self.x+', '+fmt%self.y+', '+fmt%self.z+')'

    def __eq__(self, v):
        """== operator
        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> b=Vec3(-0.3, 0.75, 0.5)
        >>> c=Vec3(-0.3, 0.75, 0.5)
        >>> print a==b
        0
        >>> print b==c
        1
        >>> print a==None
        0
        """
        global EPS
        if isinstance(v, Vec3):
            return (abs(self.x-v.x) <= EPS and
                    abs(self.y-v.y) <= EPS and
                    abs(self.z-v.z) <= EPS)
        else:
            return False

    def __ne__(self, v):
        """!= operator

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> b=Vec3(-0.3, 0.75, 0.5)
        >>> c=Vec3(-0.3, 0.75, 0.5)
        >>> print a!=b
        1
        >>> print b!=c
        0
        >>> print a!=None
        1
        """
        return not (self==v)

    def __sub__( self, v ):
        """Vector subtraction.

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> b=Vec3(-0.3, 0.75, 0.5)
        >>> print a-b
        (1.3000, -0.2500, -2.3000)
        """
        if isinstance(v, Vec3):
            return Vec3(self.x-v.x, self.y-v.y, self.z-v.z)
        else:
            raise TypeError, "unsupported operand type for -"

    def __add__( self, v ):
        """Vector addition.

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> b=Vec3(-0.3, 0.75, 0.5)
        >>> print a+b
        (0.7000, 1.2500, -1.3000)
        """        
        if isinstance(v, Vec3):
            return Vec3(self.x+v.x, self.y+v.y, self.z+v.z)
        else:
            raise TypeError, "unsupported operand type for +"
        
    def __mul__(self, other):
        """Multiplication with a scalar or dot product.

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> b=Vec3(-0.3, 0.75, 0.5)
        >>> print a*2.0
        (2.0000, 1.0000, -3.6000)
        >>> print 2.0*a
        (2.0000, 1.0000, -3.6000)
        >>> print a*b
        -0.825
        """
        T = type(other)
        # Vec3*scalar
        if T==types.FloatType or T==types.IntType or T==types.LongType:
            return Vec3(self.x*other, self.y*other, self.z*other)
        # Vec3*Vec3
        if isinstance(other, Vec3):
            return self.x*other.x + self.y*other.y + self.z*other.z
        # unsupported
        else:
            # Try to delegate the operation to the other operand
            if getattr(other,"__rmul__",None)!=None:
                return other.__rmul__(self)
            else:
                raise TypeError, "unsupported operand type for *"

    __rmul__ = __mul__

    def __div__(self, v):
        """Division by scalar

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> print a/2.0
        (0.5000, 0.2500, -0.9000)
        """
        T = type(v)
        # Vec3/scalar
        if T==types.FloatType or T==types.IntType or T==types.LongType:
            return Vec3(self.x/v, self.y/v, self.z/v)
        # unsupported
        else:
            raise TypeError, "unsupported operand type for /"

    def __iadd__(self, v):
        """Inline vector addition.

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> b=Vec3(-0.3, 0.75, 0.5)
        >>> a+=b
        >>> print a
        (0.7000, 1.2500, -1.3000)
        """
        if isinstance(v, Vec3):
            self.x+=v.x
            self.y+=v.y
            self.z+=v.z
            return self
        else:
            raise TypeError, "unsupported operand type for +="

    def __isub__(self, v):
        """Inline vector subtraction.

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> b=Vec3(-0.3, 0.75, 0.5)
        >>> a-=b
        >>> print a
        (1.3000, -0.2500, -2.3000)
        """
        if isinstance(v, Vec3):
            self.x-=v.x
            self.y-=v.y
            self.z-=v.z
            return self
        else:
            raise TypeError, "unsupported operand type for -="

    def __imul__(self, v):
        """Inline multiplication (only with scalar)

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> a*=2.0
        >>> print a
        (2.0000, 1.0000, -3.6000)
        """
        T = type(v)
        # Vec3*=scalar
        if T==types.FloatType or T==types.IntType or T==types.LongType:
            self.x*=v
            self.y*=v
            self.z*=v
            return self
        else:
            raise TypeError, "unsupported operand type for *="

    def __idiv__(self, v):
        """Inline division with scalar

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> a/=2.0
        >>> print a
        (0.5000, 0.2500, -0.9000)
        """
        T = type(v)
        # Vec3/=scalar
        if T==types.FloatType or T==types.IntType or T==types.LongType:
            self.x/=v
            self.y/=v
            self.z/=v
            return self
        else:
            raise TypeError, "unsupported operand type for /="

    def length(self):
        """Return the length of the vector.

        v.length() is equivalent to abs(v).

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> print a.length()
        2.11896201004
        """
        return math.sqrt(self*self)

    def cross(self, v):
        """Cross product.

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> b=Vec3(-0.3, 0.75, 0.5)
        >>> c=a.cross(b)
        >>> print c
        (1.6000, 0.0400, 0.9000)
        """
        
        if isinstance(v, Vec3):
            return Vec3(self.y*v.z-self.z*v.y,
                        self.z*v.x-self.x*v.z,
                        self.x*v.y-self.y*v.x)
        else:
            raise TypeError, "unsupported operand type for cross()"

    def normalize(self):
        """Return normalized vector.

        >>> a=Vec3(1.0, 0.5, -1.8)
        >>> print a.normalize()
        (0.4719, 0.2360, -0.8495)
        """
        nlen = 1.0/math.sqrt(self*self)
        return Vec3(self.x*nlen, self.y*nlen, self.z*nlen)

######################################################################
def _test():
    import doctest, basics
    failed, total = doctest.testmod(basics)
    print "%d/%d failed" % (failed, total)

if __name__=="__main__":

    _test()

#    a = Vec3(1,2,3.03)
#    b = Vec3("-2,0.5,1E10")

#    print a.angle(b)
