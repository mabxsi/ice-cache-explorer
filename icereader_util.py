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
import os
import gzip
import struct
import numpy as np
from consts import CONSTS

def log_error( f0, f1, sysexc ):
    print 'ERROR:\n   Function: %s (%s)\n   Caller: %s (%s at line %d):\n   EXCEPTION: %s : %s' % (f0.f_code.co_name,f0.f_code.co_filename,f1.f_code.co_name,f1.f_code.co_filename,f1.f_lineno,sysexc[0],sysexc[1])
    
def traceit():
    try:
        raise "foo"
    except:
        import sys, traceback
        fp = sys.exc_traceback.tb_frame
        while fp:
            print fp.f_code.co_filename, fp.f_lineno, fp.f_code.co_name
            fp = fp.f_back
            
class DataAccessor(object):
    def validate_data( self, data ):
        return len(data) > 1 and len(data[0]) > 0
        
    def read( self, file ):
        pass
    
    def format( self, array ):
        pass

    def size( self ):
        """number of bytes to read"""
        pass
    
    def length(self):
        """number of elements of type self.type()"""
        return 0

    def type(self):
        """array data type"""
        return np.int32

class DataAccessorLong(DataAccessor):
    def read( self, file ):
        try:
            (value,) = struct.unpack( 'I', file.read( 4 ) )
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )

        return False

    def size( self ):
        return 4

    def length(self):
        return 1
    
    def type(self):
        return np.int32
        
    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: value=%d\n' ) % (i,data[0])
        return buf

class DataAccessorShape(DataAccessorLong):
    pass
    
class DataAccessorBool(DataAccessorLong):
    def read( self, file ):
        try:
            value = bool( DataAccessorLong.read( self, file ) )
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return False

    def size( self ):
        return DataAccessorLong.size( self )

    def type(self):
        return np.bool

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: value=%d\n' ) % (i,data[0])
        return buf

class DataAccessorFloat(DataAccessor):
    def read( self, file ):
        try:
            value = struct.unpack( 'f', file.read( 4 ) )
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return ()

    def size( self ):
        return 4

    def length(self):
        return 1
    
    def type(self):
        return np.float64

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        for i,data in enumerate(array):
            buf += ( '%d: value=%f\n' ) % (i,data[0])
        return buf

class DataAccessorCustomType(DataAccessor):
    pass
    
class DataAccessorString(DataAccessor):
    def read( self, file ):        
        try:
            (length,) = struct.unpack( 'I', file.read( 4 ))
            
            if (length % 4) > 0 :
                length += 4- (length % 4);

            value = file.read( length )            
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return ''

    def size( self ):
        return 0

    def length(self):
        return 1
    
    def type(self):
        return np.uint16

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: string=%s\n' ) % (i,data[0])
        return buf


class DataAccessorVector2(DataAccessor):
    def read( self, file ):
        try:
            value = struct.unpack( '2f', file.read( 8 ) )
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return ()

    def size( self ):
        return 8

    def length(self):
        return 2
    
    def type(self):
        return np.int32

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: x=%f y=%f\n' ) % (i,data[0],data[1])
        return buf

class DataAccessorVector3(DataAccessor):
    def read( self, file ):
        try:
            value = struct.unpack( '3f', file.read( 12 ) )
            #print '>>> %s' % str(value)
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return ()

    def size( self ):
        return 12

    def length(self):
        return 3
    
    def type(self):
        return np.float64

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: x=%f y=%f z=%f\n' ) % (i,data[0],data[1],data[2])
        return buf

class DataAccessorVector4(DataAccessor):
    def read( self, file ):
        try:
            value = struct.unpack( '4f', file.read( 16 ) )
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return ()
    
    def size( self ):
        return 16

    def length(self):
        return 4
    
    def type(self):
        return np.float64

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: x=%f y=%f z=%f w=%f\n' ) % (i,data[0],data[1],data[2],data[3])
        return buf

class DataAccessorQuaternion(DataAccessor):
    def read( self, file ):
        try:
            value = struct.unpack( '4f', file.read( 16 ) )
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return ()

    def size( self ):
        return 16

    def length(self):
        return 4
    
    def type(self):
        return np.float64

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: w=%f x=%f y=%f z=%f\n' ) % (i,data[0],data[1],data[2],data[3])
        return buf

class DataAccessorRotation(DataAccessorQuaternion):
    def __init__(self):
        pass
    
class DataAccessorColor4(DataAccessor):
    def read( self, file ):
        try:
            value = struct.unpack( '4f', file.read( 16 ) )
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return ()

    def size( self ):
        return 16

    def length(self):
        return 4
    
    def type(self):
        return np.float64

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            if len(data) > 1:
                buf += ( '%d: r=%f g=%f b=%f a=%f\n' ) % (i,data[0],data[1],data[2],data[3])
            else:
                buf += ( '%d: no data\n' ) % i
        return buf

class DataAccessorMatrix33(DataAccessor):
    def read( self, file ):
        try:
            value = struct.unpack( '9f', file.read( 36 ) )
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return ()

    def size( self ):
        return 36

    def length(self):
        return 9
    
    def type(self):
        return np.float64

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: m[0][0]=%f m[0][1]=%f m[0][2]=%f\n' ) % (i,data[0],data[1],data[2])
            buf += ( '%d: m[1][0]=%f m[1][1]=%f m[1][2]=%f\n' ) % (i,data[3],data[4],data[5])
            buf += ( '%d: m[2][0]=%f m[2][1]=%f m[2][2]=%f\n' ) % (i,data[6],data[7],data[8])
        return buf

class DataAccessorMatrix44(DataAccessor):
    def read( self, file ):
        try:
            value = struct.unpack( '16f', file.read( 64 ) )
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return ()

    def size( self ):
        return 64

    def length(self):
        return 16
    
    def type(self):
        return np.float64

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: m[0][0]=%f m[0][1]=%f m[0][2]=%f m[0][3]=%f\n' ) % (i,data[0],data[1],data[2],data[3])
            buf += ( '%d: m[1][0]=%f m[1][1]=%f m[1][2]=%f m[1][3]=%f\n' ) % (i,data[4],data[5],data[6],data[7])
            buf += ( '%d: m[2][0]=%f m[2][1]=%f m[2][2]=%f m[2][3]=%f\n' ) % (i,data[8],data[9],data[10],data[11])
            buf += ( '%d: m[3][0]=%f m[3][1]=%f m[3][2]=%f m[3][3]=%f\n' ) % (i,data[12],data[13],data[14],data[15])
        return buf


dataAccessorMap = { 
    CONSTS.siICENodeDataBool           : DataAccessorBool(), 
    CONSTS.siICENodeDataColor4         : DataAccessorColor4(), 
    CONSTS.siICENodeDataCustomType     : DataAccessorCustomType(), 
    CONSTS.siICENodeDataFloat          : DataAccessorFloat(), 
    CONSTS.siICENodeDataLong           : DataAccessorLong(), 
    CONSTS.siICENodeDataMatrix33       : DataAccessorMatrix33(), 
    CONSTS.siICENodeDataMatrix44       : DataAccessorMatrix44(), 
    CONSTS.siICENodeDataQuaternion     : DataAccessorQuaternion(), 
    CONSTS.siICENodeDataRotation       : DataAccessorRotation(), 
    CONSTS.siICENodeDataString         : DataAccessorString(), 
    CONSTS.siICENodeDataVector2        : DataAccessorVector2(), 
    CONSTS.siICENodeDataVector3        : DataAccessorVector3(), 
    CONSTS.siICENodeDataVector4        : DataAccessorVector4()
}

"""
dataAccessor2DMap = { 
    CONSTS.siICENodeDataBool           : DataAccessor2DBool(), 
    CONSTS.siICENodeDataColor4         : DataAccessor2DColor4(), 
    CONSTS.siICENodeDataCustomType     : DataAccessor2DCustomType(), 
    CONSTS.siICENodeDataFloat          : DataAccessor2DFloat(), 
    CONSTS.siICENodeDataLong           : DataAccessor2DLong(), 
    CONSTS.siICENodeDataMatrix33       : DataAccessor2DMatrix33(), 
    CONSTS.siICENodeDataMatrix44       : DataAccessor2DMatrix44(), 
    CONSTS.siICENodeDataQuaternion     : DataAccessor2DQuaternion(), 
    CONSTS.siICENodeDataRotation       : DataAccessor2DRotation(), 
    CONSTS.siICENodeDataString         : DataAccessor2DString(), 
    CONSTS.siICENodeDataVector2        : DataAccessor2DVector2(), 
    CONSTS.siICENodeDataVector3        : DataAccessor2DVector3(), 
    CONSTS.siICENodeDataVector4        : DataAccessor2DVector4() 
}
"""
dataAccessor2DMap = {0:None}
    
class DataAccessorPool(object):
    def __init__(self):
        pass
    
    def accessor( self, datatype, structtype ):
        if structtype == CONSTS.siICENodeStructureSingle:
            return dataAccessorMap[ datatype ]
        elif structtype == CONSTS.siICENodeStructureArray:
            return dataAccessor2DMap[ datatype ]
        return None

dataAccessorPool = DataAccessorPool()

if __name__ == '__main__':

    quat = dataAccessorPool.accessor(CONSTS.siICENodeDataQuaternion, CONSTS.siICENodeStructureSingle )
    print dir(quat)
    s = quat.format( [[1,2,3,4]] )
    print s
    
    color4 = dataAccessorPool.accessor(CONSTS.siICENodeDataColor4, CONSTS.siICENodeStructureSingle )
    print dir(color4)
    s = color4.format( [[1,2,3,4]] )
    print s