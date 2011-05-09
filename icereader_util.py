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
import os
import gzip
import struct
import numpy as np
from cStringIO import StringIO 
from consts import CONSTS
import re
import h5py as h5

__all__ = [
    'ICECacheDataReadError',
    'dataAccessorPool',
    'datatype_to_string',
    'structtype_to_string',
    'contexttype_to_string',
    'categorytype_to_string',
    'objtype_to_string',
    'report_error',
    'ICECacheFileHandler',
    'get_files_from_cache_folder',
    'get_export_file_path',
    'get_files',
    'to_sih5',
    'to_ascii',
    'attribs_to_str',
    'traceit',
    'EXT'
    ]

EXT = []
EXT.append( '.txt')
EXT.append( '.sih5' )
EXT.append( '.icecache' )

def get_files_from_cache_folder( dir ):
    """ Get all cache files from dir and sort them by frame number """                
    files = []
    # grab the files
    for dirname, dirnames, filenames in os.walk(dir):
        if dirname == dir:
            filenames = filter( lambda x: x.endswith( '.icecache' ) or x.endswith( '.sih5' ) or x.endswith( '.hdf5' ), filenames )        
            for filename in filenames:
                files.append( os.path.join(dirname, filename) ) 
    
    return get_files( files )
    
def get_files( files ):
    """ sort function by the cache frame number embedded in the file name """
    def cmp_by_num (x,y):
        def get_nums(str): 
            ext = os.path.splitext( x )[1]            
            idx = -1
            if ext == '.sih5':
                idx = -2
            return float(re.findall(r'\d+',str)[idx])
        
        nx = get_nums(x)
        ny = get_nums(y)
        if nx < ny:
            return -1
        elif nx > ny:
            return 1
        return 0
    
    files.sort( cmp_by_num )
 
    if files == []:
        # no files to process
        return ()
        
    # extract start and end cache number    
    first = os.path.splitext( files[0] )[0]
    last = os.path.splitext( files[-1] )[0]
    start = int(re.findall(r'\d+',first)[-1])        
    end = int(re.findall(r'\d+',last)[-1])
    
    if end > len(files):
        end = (start + len(files)) -1 

    return (files,start,end)

def get_export_file_path( dst, fname, ext='.txt' ):
    """ create export file path """
    if ext != None:
        filepath = os.path.join(dst, os.path.basename(fname)) + ext
    else:
        filepath = os.path.join(dst, os.path.basename(fname))
    return filepath

def to_sih5( target, src ):
    """ 
    Copy src to sih5 (HDF5) target object. 
    target: sih5 file object or full file path
    src: container object with ICE cache data. Typically a ICEReader, H5Reader or any object supporting a similar interface.
    """
    if target == None:
        return

    h5_obj = None
    ish5 = isinstance(target, h5.highlevel.File)
    if ish5:
        h5_obj = target
    else:
        try:
            h5_obj = h5.File( target, 'w' )
        except:
            raise Exception('Error exporting to SIH5: invalid arguments')
            return
    
    # create the header group
    hg = h5_obj.create_group('HEADER')
        
    hg.attrs['name'] = src.header['name']
    hg.attrs['version'] = src.header['version']
    hg.attrs['type'] = src.header['type']
    hg.attrs['particle_count'] = src.header['particle_count']
    hg.attrs['edge_count'] = src.header['edge_count']
    hg.attrs['polygon_count'] = src.header['polygon_count']
    hg.attrs['sample_count'] = src.header['sample_count']
    hg.attrs['blob_count'] = src.header['blob_count']
    hg.attrs['attribute_count'] = src.header['attribute_count']
    hg.attrs['substeps_count'] = src.header['substeps_count']
            
    attrib_group = h5_obj.create_group('ATTRIBS')
    for a in src.attributes:
        g = attrib_group.create_group(a['name'])
        g.attrs['name'] = a['name']
        g.attrs['datatype'] = a['datatype']
        g.attrs['structtype'] = a['structtype']
        g.attrs['contexttype'] = a['contexttype']
        g.attrs['objid'] = a['objid']
        g.attrs['category'] = a['category']
        g.attrs['ptlocator_size'] = a['ptlocator_size']
        g.attrs['blobtype_count'] = a['blobtype_count']
        g.attrs['blobtype_names'] = a['blobtype_names']
        g.attrs['isconstant'] = a['isconstant']
            
        # data set
        data_array = a.data
        if len(data_array):
            g.create_dataset('Data', data = data_array, compression='gzip', compression_opts=9, shuffle=True )

    if not ish5:
        # close file only if we opened the file
        h5_obj.close()
    
def to_ascii( target, src ):    
    """ 
    Copy src to file as ascii format as defined by DataAccessor.
    target: Full file path
    src: container object with ICE cache data. Typically a ICEReader, H5Reader or any object supporting a similar interface.
    """
    
    f = open( target, 'w' )        
    f.write( str(src.header) )
    f.write( '\n' )
                
    for a in src.attributes:
        # description
        f.write( str(a) )
        f.flush()

        # data
        accessor = dataAccessorPool.accessor(a['datatype'],a['structtype'])
        
        data_array = a.data
        if len(data_array):     
            if a['isconstant'] == True:
                f.write( accessor.format( [data_array[0]] ) )
            else:
                f.write( accessor.format( data_array ) )

        f.write( '\n' )
        f.flush()
    
    f.close()

def attribs_to_str( dict ):
    s = '[Attribute info]\n'
    for a in dict:
        s += '%s = %s\n' %( a, str(dict[a]) )
    try:
        for i in range(dict['blobtype_count']):
            s += ("   blob %d = %s\n") % (i,dict['blobtype_name'](i))
    except:
        pass
    return s

class DataAccessor(object):
    """ICE cache data accesor base class"""
    def __init__(self):
        self.handler = None
    
    def validate_data( self, data ):
        return len(data) > 0 and len(data[0]) > 0
        
    def read( self ):
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
    
    def allocate_array( self, elem_count ):
        """allocate to store data read with this accessor"""
        data = np.zeros( (elem_count, self.length() ), self.type() )
        return data

    def read_block( self, chunksize ):
        """ return a block of data of a specific size """
        self.handler.read_block( chunksize * self.size() )
        
    def release_block( self ):
        self.handler.release_block()

class DataAccessorLong(DataAccessor):
    def read( self ):
        return self.handler.read_long( )
        
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

class DataAccessorShape(DataAccessor):
    """ not supported, just read the values and leave """
    def read( self ):        
        trivial = self.handler.read_bool()
        shapetype = self.handler.read_long()
        if long(shapetype) == CONSTS.siICEShapeReference:
            refid = self.handler.read_ulong()
            hasbranch = self.handler.read_bool()
            hasremapinfo = self.handler.read_bool()
            
            if bool(hasremapinfo) == True:
                targetpath = self.handler.read_name()
                modelguid = self.handler.read_name()
        elif long(shapetype) == CONSTS.siICEShapeInstance:
            shapeindex = self.handler.read_ulong()
        # just return the type for now
        return shapetype
        
    def size( self ):
        """number of bytes """
        return 4

    def length(self):
        """ number of shape """
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
        
    def read_block( self, chunksize ):
        """ just use the original file ptr """
        self.handler.block = None

    def release_block( self ):
        """ there is no block to release """
        pass

class DataAccessorBool(DataAccessor):
    def read( self ):
        value = self.handler.read_bool( )
        return value
        
    def size( self ):
        return np.int32

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
    def read( self ):
        value = self.handler.read_float( )
        return value
        
    def size( self ):
        return 4

    def length(self):
        return 1
    
    def type(self):
        return np.float32

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        for i,data in enumerate(array):
            buf += ( '%d: value=%0.6f\n' ) % (i,data[0])
        return buf

class DataAccessorCustomType(DataAccessor):
    pass
    
class DataAccessorString(DataAccessor):
    def read( self ):        
        value = self.handler.read_name( )            
        return value

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
    def read( self ):
        value = self.handler.read( '2f', 8 )
        return value
        
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
            buf += ( '%d: x=%0.6f y=%0.6f\n' ) % (i,data[0],data[1])
        return buf

class DataAccessorVector3(DataAccessor):
    def read( self ):
        value = self.handler.read( '3f', 12 )
        return value

    def size( self ):
        return 12

    def length(self):
        return 3
    
    def type(self):
        return np.float32

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: x=%0.6f y=%0.6f z=%0.6f\n' ) % (i,data[0],data[1],data[2])
        return buf

class DataAccessorVector4(DataAccessor):
    def read( self ):
        value = self.handler.read( '4f', 16 )
        return value
    
    def size( self ):
        return 16

    def length(self):
        return 4
    
    def type(self):
        return np.float32

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: x=%0.6f y=%0.6f z=%0.6f w=%0.6f\n' ) % (i,data[0],data[1],data[2],data[3])
        return buf

class DataAccessorQuaternion(DataAccessor):
    def read( self ):
        value = self.handler.read( '4f', 16 )
        return value

    def size( self ):
        return 16

    def length(self):
        return 4
    
    def type(self):
        return np.float32

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: w=%0.6f x=%0.6f y=%0.6f z=%0.6f\n' ) % (i,data[0],data[1],data[2],data[3])
        return buf

class DataAccessorRotation(DataAccessorQuaternion):
    def __init__(self):
        pass
    
class DataAccessorColor4(DataAccessor):
    def read( self ):
        return self.handler.read( '4f', 16 )

    def size( self ):
        return 16

    def length(self):
        return 4
    
    def type(self):
        return np.float32

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            if len(data) > 1:
                buf += ( '%d: r=%0.6f g=%0.6f b=%0.6f a=%0.6f\n' ) % (i,data[0],data[1],data[2],data[3])
            else:
                buf += ( '%d: no data\n' ) % i
        return buf

class DataAccessorMatrix33(DataAccessor):
    def read( self ):
        value = self.handler.read( '9f', 36 )            
        return value

    def size( self ):
        return 36

    def length(self):
        return 9
    
    def type(self):
        return np.float32

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: m[0][0]=%0.6f m[0][1]=%0.6f m[0][2]=%0.6f\n' ) % (i,data[0],data[1],data[2])
            buf += ( '%d: m[1][0]=%0.6f m[1][1]=%0.6f m[1][2]=%0.6f\n' ) % (i,data[3],data[4],data[5])
            buf += ( '%d: m[2][0]=%0.6f m[2][1]=%0.6f m[2][2]=%0.6f\n' ) % (i,data[6],data[7],data[8])
        return buf

class DataAccessorMatrix44(DataAccessor):
    def read( self ):
        value = self.handler.read( '16f', 64 )
        return value

    def size( self ):
        return 64

    def length(self):
        return 16
    
    def type(self):
        return np.float32

    def format( self, array ):
        buf = ''
        if self.validate_data(array) == False:
            return '<no data>\n'
        
        for i,data in enumerate(array):
            buf += ( '%d: m[0][0]=%0.6f m[0][1]=%0.6f m[0][2]=%0.6f m[0][3]=%0.6f\n' ) % (i,data[0],data[1],data[2],data[3])
            buf += ( '%d: m[1][0]=%0.6f m[1][1]=%0.6f m[1][2]=%0.6f m[1][3]=%0.6f\n' ) % (i,data[4],data[5],data[6],data[7])
            buf += ( '%d: m[2][0]=%0.6f m[2][1]=%0.6f m[2][2]=%0.6f m[2][3]=%0.6f\n' ) % (i,data[8],data[9],data[10],data[11])
            buf += ( '%d: m[3][0]=%0.6f m[3][1]=%0.6f m[3][2]=%0.6f m[3][3]=%0.6f\n' ) % (i,data[12],data[13],data[14],data[15])
        return buf

class DataAccessorPointLocator(DataAccessor):
    def read( self ):
        self.stream_size = self.handler.read_ulong( )
        (value,) = self.handler.read( 'L', stream_size )
        return value

    def size( self ):
        return 4

    def length(self):
        return self.stream_size
    
    def type(self):
        return np.int32

    def format( self, array ):
        return '<no data>\n'

datatype_to_string_map = { 
    CONSTS.siICENodeDataBool            : 'siICENodeDataBool', 
    CONSTS.siICENodeDataColor4          : 'siICENodeDataColor4', 
    CONSTS.siICENodeDataCustomType      : 'siICENodeDataCustomType', 
    CONSTS.siICENodeDataFloat           : 'siICENodeDataFloat', 
    CONSTS.siICENodeDataLong            : 'siICENodeDataLong', 
    CONSTS.siICENodeDataMatrix33        : 'siICENodeDataMatrix33', 
    CONSTS.siICENodeDataMatrix44        : 'siICENodeDataMatrix44', 
    CONSTS.siICENodeDataQuaternion      : 'siICENodeDataQuaternion', 
    CONSTS.siICENodeDataRotation        : 'siICENodeDataRotation', 
    CONSTS.siICENodeDataString          : 'siICENodeDataString', 
    CONSTS.siICENodeDataVector2         : 'siICENodeDataVector2', 
    CONSTS.siICENodeDataVector3         : 'siICENodeDataVector3', 
    CONSTS.siICENodeDataVector4         : 'siICENodeDataVector4',
    CONSTS.siICENodeDataShape           : 'siICENodeDataShape'
}

structtype_to_string_map = { 
    CONSTS.siICENodeStructureSingle     : 'siICENodeStructureSingle',
    CONSTS.siICENodeStructureArray      : 'siICENodeStructureArray'
}

contexttype_to_string_map = { 
    CONSTS.siICENodeContextComponent0D  : 'siICENodeContextComponent0D',
    CONSTS.siICENodeContextComponent0D2D    : 'siICENodeContextComponent0D2D',
    CONSTS.siICENodeContextComponent1D  : 'siICENodeContextComponent1D',
    CONSTS.siICENodeContextComponent2D  : 'siICENodeContextComponent2D',
    CONSTS.siICENodeContextElementGenerator : 'siICENodeContextElementGenerator',
    CONSTS.siICENodeContextSingleton    : 'siICENodeContextSingleton'
}

categorytype_to_string_map = { 
    CONSTS.siICEAttributeCategoryUnknown   : 'siICEAttributeCategoryUnknown',
    CONSTS.siICEAttributeCategoryBuiltin   : 'siICEAttributeCategoryBuiltin',
    CONSTS.siICEAttributeCategoryCustom    : 'siICEAttributeCategoryCustom'
}

objtype_to_string_map = {
    CONSTS.siICENodeObjectPointCloud : 'siICENodeObjectPointCloud',
    CONSTS.siICENodeObjectPolygonMesh : 'siICENodeObjectPolygonMesh',
    CONSTS.siICENodeObjectNurbsMesh : 'siICENodeObjectNurbsMesh',
    CONSTS.siICENodeObjectNurbsCurve : 'siICENodeObjectNurbsCurve'
}

def datatype_to_string( type ):
    try:
        return datatype_to_string_map[ type ]
    except:
        # unknown
        return str(type)

def structtype_to_string( type ):
    try:
        return structtype_to_string_map[ type ]
    except:
        # unknown
        return str(type)

def contexttype_to_string( type ):
    try:
        return contexttype_to_string_map[ type ]
    except:
        # unknown
        return str(type)

def categorytype_to_string( type ):
    try:
        return categorytype_to_string_map[ type ]
    except:
        # unknown
        return str(type)

def objtype_to_string( type ):
    try:
        return objtype_to_string_map[ type ]
    except:
        # unknown
        return str(type)

def printf( format, *args ):
    sys.stdout.write(format % args )
    
def report_error( msg, sysexc ):
    print 'EXCEPTION %s : %s' % (sysexc[0],sysexc[1])
    traceit(msg)
    
def traceit(msg):
    try:
        raise "foo"
    except:
        print 'ERROR: %s' % msg
        
        import sys, traceback
        fp = sys.exc_traceback.tb_frame
        while fp:
            print fp.f_code.co_filename, fp.f_lineno, fp.f_code.co_name
            fp = fp.f_back

class ICECacheDataReadError(Exception):
    """ICECache data read error"""
    pass

class ICECacheFileHandler( object ):
    INVALID_INT = 1
    INVALID_STRING = 'invalid string'
    ICECACHE_CHUNK_SIZE = 4000
    
    def __init__(self,file):
        self.file = file
        self.block = None

    def __str__(self):
        return ('self.file %s, self.block %s') % (self.file, self.block)
        
    def __del__(self):
        self.file.close()

    def read( self, format, size ):
        file = self.__fileptr__()
        try:
            val = struct.unpack( format, file.read( size ) )
            return val
        except:
            report_error( 'unpack %s %d' % (format,size), sys.exc_info() )
            raise ICECacheDataReadError
        return None

    def read_bytes( self, size ):
        file = self.__fileptr__()
        return file.read( size )

    def icecache_version(self):
        name = self.read_header_name( )
        version = self.read_int()
        # rewind to beginning
        self.file.seek( 0, os.SEEK_SET )
        return version

    def read_header_name( self ):
        return self.read_bytes( 8 )
    
    def read_name( self ):
        length = self.read_long( )
        
        if (length % 4) > 0 :
            length += 4- (length % 4)

        return self.read_bytes( length )
        
    def read_int(self):
        (value,) = self.read( 'i', 4 )
        return value

    def read_uint(self):
        (value,) = self.read( 'I', 4 )
        return value

    def read_ulong(self):
        (value,) = self.read( 'L', 4 )
        return value

    def read_long(self):
        (value,) = self.read( 'l', 4 )
        return value

    def read_bool(self):
        (value,) = self.read( '?', 1)
        return value

    def read_float(self):
        (value,) = self.read( 'f', 4)
        return value
        
    def read_block(self, block_size):
        self.release_block()
        self.block = StringIO( self.file.read( block_size ) )
        self.file.flush()

    def release_block(self):
        if self.block != None:
            self.block.close()
            self.block = None
            
    def close(self):
        self.file.close()
        
    def __fileptr__(self):
        file = self.file
        if self.block != None:
            file = self.block
        return file

    def chunks( self, elemCount ):
        """ 
        compute number of chunks based on the total number of elements
        """
        if elemCount < self.ICECACHE_CHUNK_SIZE:
            return [range(elemCount)]
        
        outChunks = []
        chunks = elemCount / self.ICECACHE_CHUNK_SIZE
        for i in xrange(chunks):
            outChunks.append(xrange((i)*self.ICECACHE_CHUNK_SIZE, (i+1)*self.ICECACHE_CHUNK_SIZE))
        outChunks.append(xrange( (i+1)*self.ICECACHE_CHUNK_SIZE, (i+1)*self.ICECACHE_CHUNK_SIZE + elemCount%self.ICECACHE_CHUNK_SIZE) )
        
        """
        print 'outChunks = %d' % len(outChunks)
        for i,chunk in enumerate(outChunks):
            print 'chunk %d = %d' % (i,len(chunk))
        """
        
        return outChunks

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
    CONSTS.siICENodeDataVector4        : DataAccessorVector4(),
    CONSTS.siICENodeDataShape          : DataAccessorShape()
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