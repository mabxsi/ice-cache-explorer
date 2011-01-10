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
import re
from consts import CONSTS
from icereader_util import dataAccessorPool
from icereader_util import log_error
from cStringIO import StringIO 

try:
    import numpy 
except:
    print "ERROR: numpy not installed properly."
    sys.exit()

_trace = False

def _debug( msg ):
    if _trace:
        print '*** %s ***' % msg
"""
import gc
 gc.set_debug(gc.DEBUG_LEAK)
"""

class ICEReader(object):
    INVALID_INT = 1,
    INVALID_STRING = 'invalid string',
    ICECACHE_CHUNK_SIZE = 4000
    class Header(object):
        def __init__(self):
            self.name = None
            self.version = 0
            self.type = 0
            self.particle_count = 0
            self.edge_count = 0
            self.polygon_count = 0
            self.sample_count = 0
            self.blob_count = 0
            self.attribute_count = 0

        def __str__(self):
            return  ("[Header info]\nname = %s\nversion = %d\ntype = %d\nparticle_count = %d\nedge_count = %d\npolygon_count = %d\nsample_count = %d\nblob_count = %d\nattribute_count = %d\n") % ( self.name, self.version, self.type, self.particle_count, self.edge_count, self.polygon_count, self.sample_count, self.blob_count, self.attribute_count )

    class Attribute(object):
        def __init__(self):
            self.name = None
            self.datatype = 0
            self.structtype = 0
            self.contexttype = 0
            self.objid = 0
            self.category = 0
            self.ptlocator_size = 0
            self.blobtype_count = 0
            self.blobtype_names = ()
            self.isconstant = True

        def __str__(self):
            s = ("[Attribute info]\nname = %s\ndatatype = %d\nstructtype = %d\ncontexttype = %d\nobjid = %d\ncategory = %d\nptlocator_size = %d\nis constant = %d\n") % ( self.name, self.datatype, self.structtype, self.contexttype, self.objid, self.category, self.ptlocator_size, self.isconstant )
            
            for i in range(self.blobtype_count):
                s += ("   blob %d = %s\n") % (i,self.blobtype_name(i))
                        
            #slist = [("   blob %d = %s\n") % (i,self.blobtype_name(i)) for i in range(self.blobtype_count)]
            #s = s.join(slist)             
            return s       

    def __init__(self,filename):
        """ open file and store the file pointer """
        self._filename = filename
        self._file = None        
        self._header = None
        self._attributes = None
        self._data = {}
        #self.__read_attributes_data__ = self.__read_attributes_data_pylist__
        self.__read_attributes_data__ = self.__read_attributes_data_numpy__
        
        try:
            self.file = gzip.open( self._filename, 'rb' )
        except:
            print 'invalid file %s' % filename
            
           
    def __del__(self):
        self.close()

    def filename(self):
        return self._filename
        
    def load_data(self, attributes_to_load=() ):
        self.__read_header__()
        self.__read_attributes_desc__()
        self.__read_attributes_data__( attributes_to_load )
        self.file.flush()

    def header(self):
        return self._header

    def attributes(self):
        return self._attributes

    def log_info(self, destination_folder ):

        # build log file path        
        filepath = os.path.join(destination_folder, os.path.basename(self._filename)  ) + '.txt'
                
        f = open( filepath, 'w' )        
        f.write( str(self._header) )
        f.write( '\n' )
                
        for a in self._attributes:
            # description
            s = str(a)
            f.write( s )
            f.flush()

            # data            
            accessor = dataAccessorPool.accessor(a.datatype,a.structtype)
            
            if a.name in self._data:                
                f.write( accessor.format( self._data[ a.name ] ) )
            else:
                f.write( accessor.format( [] ) )

            f.write( '\n' )
            f.flush()
            
        f.close()
            
    def close(self):
        self.file.close()

    def __getitem__( self, arg ):
        #return numpy.array( self._data[ arg ] )
        return self._data[ arg ]
        
    def __read_header__(self):        
        if self.file == None:
                return None

        try:
            self._header = ICEReader.Header()        
        
        except:
            print 'error ICEReader.Header'
        
        try:
            self._header.name = self.file.read( 8 )
            self._header.version = self.__read_int__()
            self._header.type = self.__read_int__()
            self._header.particle_count = self.__read_int__()
            self._header.edge_count = self.__read_int__()
            self._header.polygon_count = self.__read_int__()
            self._header.sample_count = self.__read_int__()
            self._header.blob_count = self.__read_int__()
            self._header.attribute_count = self.__read_int__()
        except:
            print 'error reading header'

        #_debug( self._header )
        return self._header

    def __read_attributes_desc__(self):
        if self.file == None:
            return None
        
        self._attributes = []
        for i in range(self._header.attribute_count):            
            attrib = ICEReader.Attribute()
            
            attrib.name = self.__read_string__()
            attrib.datatype = self.__read_int__()
            
            if attrib.datatype == CONSTS.siICENodeDataCustomType and self._header.version > CONSTS.siICECacheV1_1:
                attrib.blobtype_count = self.__read_int__()
                
                for i in range( attrib.blobtype_count ):
                    attrib.blobtype_names.append( self.__read_string__() )                

            attrib.structtype = self.__read_int__()
            attrib.contexttype = self.__read_int__()
            attrib.objid = self.__read_int__()
            attrib.category = self.__read_int__()

            if attrib.datatype == CONSTS.siICENodeDataLocation:
                attrib.ptlocator_size = self.__read_int__()

            #_debug( attrib )

            self._attributes.append( attrib )
        
        return self._attributes

    def __read_attributes_data_pylist__(self, to_load ):
        if self.file == None:
            return None        

        for i in range(self._header.attribute_count):    
            data = []
            attrib = self._attributes[i]            

            toKeep = False
            if attrib.name in to_load:
                toKeep = True

            #_debug( attrib )
            accessor = dataAccessorPool.accessor(attrib.datatype,attrib.structtype)
            
            if attrib.name == 'PointPosition___':
                # exception for point position attribute: constant flag is only stored once for pointposition
                attrib.isconstant = bool(self.__read_int__())
                
                buffer = StringIO(self.file.read( self._header.particle_count*accessor.size() ))
                                
                for index in range(self._header.particle_count):                  
                    data.append( accessor.read( buffer ) )
                buffer.close()                
                
                toKeep = True
            else:
                # get number of elements to read based on the attribute context
                elemCount = 0
                if attrib.contexttype == CONSTS.siICENodeContextSingleton:
                    elemCount = 1
                elif attrib.contexttype == CONSTS.siICENodeContextComponent0D:
                    elemCount = self._header.particle_count
                elif attrib.contexttype == CONSTS.siICENodeContextComponent1D:
                    elemCount = self._header.edge_count
                elif attrib.contexttype == CONSTS.siICENodeContextComponent2D:
                    elemCount = self._header.polygon_count
                elif attrib.contexttype == CONSTS.siICENodeContextComponent0D2D:
                    elemCount = self._header.sample_count
                else:
                    # no element set 
                    continue
                
                if attrib.datatype == CONSTS.siICENodeDataLocation:
                    # just skip point locators
                    size = self.__read_int__()
                    self.file.read( size )
                    continue
                
                # loop over chunks and read the attributes
                chunks = self.__chunks__( elemCount )
                #print 'chunks %d' % len(chunks)
                for chunk in chunks:                    
                    # the constant flag value should be the same for all chunks
                    attrib.isconstant = bool(self.__read_int__())     
                    if attrib.isconstant == True:
                        # read the const value
                        if toKeep:
                            print 'constant value %s %d' % (attrib.name,len(chunk))
                            # append the whole chunk to array 
                            buffer = StringIO(self.file.read( len(chunk)*accessor.size() ))
                            constVal = accessor.read( buffer )
                            for i in chunk:         
                                data.append( constVal )
                            buffer.close()
                        else:
                            try:
                                # note: seek forward seems buggy, use read instead
                                self.file.read( len(chunk)*accessor.size() )                            
                            except:
                                log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
                    else:
                        if toKeep:
                            #read all values in the chunk                        
                            buffer = StringIO(self.file.read( len(chunk)*accessor.size() ))                        
                            for index in chunk:         
                                data.append( accessor.read( buffer ) )
                            buffer.close()
                        else:
                            try:
                                # note: seek forward seems buggy, use read instead
                                self.file.read( len(chunk)*accessor.size() )                            
                            except:
                                log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )

            if toKeep:
                self._data[ attrib.name ] = data
            del data

    def __read_attributes_data_numpy__(self, to_load ):
        if self.file == None:
            return None        

        for i in range(self._header.attribute_count):    
            attrib = self._attributes[i]            

            toKeep = False
            if attrib.name in to_load:
                toKeep = True

            #_debug( attrib )
            accessor = dataAccessorPool.accessor(attrib.datatype,attrib.structtype)
            
            if attrib.name == 'PointPosition___':
                # exception for point position attribute: constant flag is only stored once for pointposition
                attrib.isconstant = bool(self.__read_int__())

                # create Nx3 array 
                try:                    
                    data = numpy.zeros( (self._header.particle_count, accessor.length() ), dtype=accessor.type() )
                except:
                    log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
                
                # load entire block in memory
                buffer = StringIO(self.file.read( self._header.particle_count*accessor.size() ))
                self.file.flush()
                for index in xrange( self._header.particle_count ):
                    try:
                        data[index] = accessor.read( buffer )
                    except:
                        log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
                        
                buffer.close()
                
                self._data[ attrib.name ] = data
            else:
                # get number of elements to read based on the attribute context
                elemCount = 0
                if attrib.contexttype == CONSTS.siICENodeContextSingleton:
                    elemCount = 1
                elif attrib.contexttype == CONSTS.siICENodeContextComponent0D:
                    elemCount = self._header.particle_count
                elif attrib.contexttype == CONSTS.siICENodeContextComponent1D:
                    elemCount = self._header.edge_count
                elif attrib.contexttype == CONSTS.siICENodeContextComponent2D:
                    elemCount = self._header.polygon_count
                elif attrib.contexttype == CONSTS.siICENodeContextComponent0D2D:
                    elemCount = self._header.sample_count
                else:
                    # no element set 
                    continue
                
                if attrib.datatype == CONSTS.siICENodeDataLocation:
                    # just skip point locators
                    size = self.__read_int__()
                    self.file.read( size )
                    continue

                if toKeep:
                    # create [elemCount X length] array of type type()
                    try:
                        data = numpy.zeros( (elemCount, accessor.length() ), accessor.type() )
                        self._data[ attrib.name ] = data
                    except:
                        log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )                                        
                
                # loop over chunks and read the attributes
                chunks = self.__chunks__( elemCount )
                #print 'chunks %d' % len(chunks)
                index = 0
                for chunk in chunks:                    
                    # the constant flag value should be the same for all chunks
                    attrib.isconstant = bool(self.__read_int__())     
                    if attrib.isconstant == True:
                        # read the const value
                        if toKeep:
                            # append the whole chunk to array 
                            buffer = StringIO(self.file.read( accessor.size() ))                            
                            self.file.flush()
                            constVal = accessor.read( buffer )
                            
                            for i in chunk:         
                                data[index] = constVal
                                index +=1                                
                            buffer.close()
                        else:
                            try:
                                # note: seek forward seems buggy, use read instead
                                self.file.read( len(chunk)*accessor.size() )          
                                self.file.flush()
                            except:
                                log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
                    else: 
                        # non-constant values
                        if toKeep:
                            #load chunk and assing all values to array
                            buffer = StringIO(self.file.read( len(chunk)*accessor.size() ))
                            self.file.flush()                            
                            for i in chunk:         
                                data[index] = accessor.read( buffer )
                                index +=1
                            buffer.close()
                        else:
                            try:
                                # note: seek forward seems buggy, use read instead
                                self.file.read( len(chunk)*accessor.size() )     
                                self.file.flush()
                            except:
                                log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
            
    def __chunks__( self, elemCount ):
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
        
        return outChunks

    def __read_string__(self):
        try:
            (length,) = struct.unpack( 'I', self.file.read( 4 ))
            
            if (length % 4) > 0 :
                length += 4- (length % 4)

            s = self.file.read( length )
            return s

        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
            
        return self.INVALID_STRING
            
    def __read_int__(self):
        try:
            (value,) = struct.unpack( 'I', self.file.read( 4 ))
            return value
        except:            
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return self.INVALID_INT
    
    def __read_vector3f__(self):
        try:
            value = struct.unpack( '3f', self.file.read( 12 ) )
            return value
        except:
            log_error( sys._getframe(0), sys._getframe(1), sys.exc_info() )
        return ()

def get_files_from_cache_folder( dir ):
    """ Get all cache files from dir and sort them by frame number """                
    files = []
    # grab the files
    for dirname, dirnames, filenames in os.walk(dir):
        for filename in filenames:
            files.append( os.path.join(dirname, filename) ) 
            
    # sort function 
    def cmp_by_num (x,y):
        def get_last_num(str): 
            return float(re.findall(r'\d+',str)[-1])
        
        nx = get_last_num(x)
        ny = get_last_num(y)
        if nx < ny:
            return -1
        elif nx > ny:
            return 1
        return 0
    
    files.sort( cmp_by_num )

    # extract start and end cache number
    start = int(re.findall(r'\d+',files[0])[-1])
    end = int(re.findall(r'\d+',files[-1])[-1])
    
    if end > len(files):
        end = (start + len(files)) -1 
    
    return (files,start,end)

def test():
    r = ICEReader( r'C:\dev\icecache_data\TEST\478.icecache' )
    #print r.file.read()

    import time
    t = time.clock()
    #r.load_data( ('Color___') )
    r.load_data( () )
    print 'array count %d' % len(r._data)
    print 'elapsed time (ms) = %f' % (time.clock()-t)
    r.log_info( r'c:\temp' )

def main():
    # load points only
    r = ICEReader( r'C:\dev\icecache_data\TEST\478.icecache' )
    r.load_data( () )

if __name__ == '__main__':
    test()
