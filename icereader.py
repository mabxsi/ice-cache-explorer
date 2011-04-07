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
from icereader_util import *

try:
    import numpy 
except:
    print "ERROR: numpy not installed properly."
    sys.exit()
   
"""
import gc
 gc.set_debug(gc.DEBUG_LEAK)
"""

class ICEReader(object):    
    def __init__(self,filename):
        """ open file and store the file pointer """
        self._filename = filename
        self._header = None
        self._attributes = None
        self._data = {}
        file = None
        try:
            file = gzip.open( self._filename, 'rb+' )
        except:
            print 'Error - Invalid file: %s' % filename
                               
        self.handler = ICECacheFileHandler( file )

    def __del__(self):
        self._header = None
        self._attributes = None
        self._data = {}
        self.handler = None

    def filename(self):
        return self._filename
        
    def load( self ):
        """ load specific attributes of the underlying cache file """
        try:
            self.read_header()
            self.read_attributes_desc()
            self.read_attributes_data()
            self.handler.file.flush()
        except ICECacheVersionError:
            print 'Error - ICE Cache version not supported'
        
        if self._header == None:
            raise ICECacheDataReadError

    def header(self):
        return self._header

    def attributes(self):
        return self._attributes

    def find_attribute( self, name ):
        for a in self._attributes:
            if a.name == name:
                return a
        return None
    
    def export(self, destination_folder ):                
        try:
            # load the requested attributes
            self.load( )
        except:
            return
        filepath = self.get_export_file_path( destination_folder )
        self._export( filepath )        
    
    def get_export_file_path( self, destination_folder ):
        """ create export folder """
        filepath = os.path.join(destination_folder, os.path.basename(self._filename)  ) + '.txt'
        return filepath

    def close(self):
        del self.handler
        self.handler = None

    def _export( self, export_file_path ):                
        """ export the underlying file to ascii """
        f = open( export_file_path, 'w' )        
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
                data_array = self._data[ a.name ]
                if a.isconstant == True:
                    data_array = [ self._data[ a.name ][0] ]
                f.write( accessor.format( data_array ) )

            f.write( '\n' )
            f.flush()
            
        f.close()
            
    def __getitem__( self, arg ):
        """ return data buffer by name """
        return self._data[ arg ]

    # Internals
    def read_header(self):        
        """ Read header section. Supported versions are 102 and 103. """
        try:            
            v = self.handler.icecache_version()            
            if v == CONSTS.siICECacheV102:                
                self._header = HeaderV102()        
            elif v == CONSTS.siICECacheV103:
                self._header = HeaderV103()
            else:
                raise ICECacheVersionError        
        except:
            print 'Error - ICE Cache version not supported'
            return
        
        try:
            self._header.read( self.handler )            
        except:
            report_error( 'self._header', sys.exc_info() )
            raise Exception

        return self._header

    def read_attributes_desc(self):       
        """ Read all attribute descriptions """
        if self._header == None:
            return None        
        
        self._attributes = []
        for i in range(self._header.attribute_count):            
            attrib = Attribute()        
            attrib.read( self.handler )            
            self._attributes.append( attrib )
        
        return self._attributes

    def read_attributes_data( self ):
        """ Read all attributes data. """
        if self._header == None:
            return None        

        if self._header.particle_count == 0:
            return None
                
        for i in range(self._header.attribute_count):    
            attrib = self._attributes[i]            
            try:
                accessor = dataAccessorPool.accessor( attrib.datatype, attrib.structtype )
                accessor.handler = self.handler
            except:
                raise ICECacheDataAccessorError 
                
            if attrib.name == 'PointPosition___':
                attrib.isconstant = bool(self.handler.read_int())
                
                # create Nx3 array 
                try:                    
                    data = accessor.allocate_array( self._header.particle_count )
                except:
                    report_error( 'PointPosition accessor.allocate_array', sys.exc_info() )                    
                    raise Exception
                
                # load entire block in memory                
                accessor.read_block( self._header.particle_count )
                for index in xrange( self._header.particle_count ):
                    try:
                        data[index] = accessor.read( )
                    except:
                        report_error( 'load entire block in memory', sys.exc_info() )
                        raise Exception 
                                           
                accessor.release_block()                
                self._data[ attrib.name ] = data
            else:
                # Process other attributes
                
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
                    accessor.read( )
                    continue
                
                # get required nb of chunks to accomodate elemCount values
                chunks = self.handler.chunks( elemCount )
                index = 0
                for chunk in chunks:                    
                    # Note: the constant flag value is stored per chunk, which is a shame as the const flag will always be the same.
                    # Therefore we need to read 4 extra bytes at every chunk
                    attrib.isconstant = bool(self.handler.read_int())

                    # create [elemCount X accessor.length()] array of type accessor.type()
                    try:
                        if not attrib.name in self._data:
                            size = elemCount
                            if attrib.isconstant:
                                size = 1
                            data = accessor.allocate_array( size )
                            self._data[ attrib.name ] = data
                    except:
                        report_error( 'create [elemCount X length] array of type type()', sys.exc_info() )
                        raise Exception
                    
                    if attrib.isconstant == True:
                        # read the const value
                        accessor.read_block( 1 )
                        data[0] = accessor.read( )                            
                        accessor.release_block()                        
                    else: 
                        # non-constant values
                        accessor.read_block( len(chunk) )                            
                        for i in chunk:
                            try:
                                data[index] = accessor.read( )
                            except:
                                    report_error( 'error reading:\n%s' % attrib, sys.exc_info() )
                            index +=1
                        accessor.release_block()
                    
def get_files_from_cache_folder( dir ):
    """ Get all cache files from dir and sort them by frame number """                
    files = []
    # grab the files
    for dirname, dirnames, filenames in os.walk(dir):
        filenames = filter( lambda x: x.endswith('.icecache'), filenames )        
        for filename in filenames:
            files.append( os.path.join(dirname, filename) ) 
    
    return get_files( files )
    
def get_files( files ):
    """ sort function by the cache frame number embedded in the file name """
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

    if files == []:
        # no files to process
        return ()
        
    # extract start and end cache number    
    start = int(re.findall(r'\d+',files[0])[-1])
    end = int(re.findall(r'\d+',files[-1])[-1])
    
    if end > len(files):
        end = (start + len(files)) -1 

    return (files,start,end)

def is_valid_file( cachefile ):
    return cachefile.endswith('.icecache')
    
class HeaderV102(object):
    """ Version 102 ICE cache object """
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

    def read( self, handler ):
        self.name = handler.read_header_name( )
        self.version = handler.read_int( )
        self.type = handler.read_int( )
        self.particle_count = handler.read_int( )
        self.edge_count = handler.read_int( )
        self.polygon_count = handler.read_int( )
        self.sample_count = handler.read_int( )
        self.blob_count = handler.read_int( )
        self.attribute_count = handler.read_int( )

    def __str__(self):
        return  ("[Header info]\nname = %s\nversion = %d\ntype = %s\nparticle_count = %d\nedge_count = %d\npolygon_count = %d\nsample_count = %d\nblob_count = %d\nattribute_count = %d\n") % ( self.name, self.version, objtype_to_string(self.type), self.particle_count, self.edge_count, self.polygon_count, self.sample_count, self.blob_count, self.attribute_count )

class HeaderV103(object):
    """ Version 103 ICE cache object """
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
        self.substepscount = 0

    def read( self, handler ):
        self.name = handler.read_header_name( )
        self.version = handler.read_int( )
        self.type = handler.read_int( )
        self.particle_count = handler.read_int( )
        self.edge_count = handler.read_int( )
        self.polygon_count = handler.read_int( )
        self.sample_count = handler.read_int( )
        self.substepscount = handler.read_int( )
        self.blob_count = handler.read_int( )
        self.attribute_count = handler.read_int( )

    def __str__(self):
        return  ("[Header info]\nname = %s\nversion = %d\ntype = %s\nparticle_count = %d\nedge_count = %d\npolygon_count = %d\nsample_count = %d\nblob_count = %d\nattribute_count = %d\nsubstepscount = %d\n\n") % ( self.name, self.version, objtype_to_string(self.type), self.particle_count, self.edge_count, self.polygon_count, self.sample_count, self.blob_count, self.attribute_count, self.substepscount )

class Attribute(object):
    """ ICECache Attribute object """
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

    def read( self, handler ):
        self.name = handler.read_name()
        self.datatype = handler.read_int()
        
        if self.datatype == CONSTS.siICENodeDataCustomType:
            self.blobtype_count = handler.read_ulong()            
            for i in range( self.blobtype_count ):
                attrib.blobtype_names.append( handler.read_name() )                

        self.structtype = handler.read_int()
        self.contexttype = handler.read_int()
        self.objid = handler.read_int()
        self.category = handler.read_int()

        if self.datatype == CONSTS.siICENodeDataLocation:
            self.ptlocator_size = handler.read_ulong()
        
    def __str__(self):
        s = ("[Attribute info]\nname = %s\ndatatype = %s\nstructtype = %s\ncontexttype = %s\nobjid = %d\ncategory = %s\nptlocator_size = %d\nis constant = %d\n\n") % ( self.name, datatype_to_string(self.datatype), structtype_to_string(self.structtype), contexttype_to_string(self.contexttype), self.objid, categorytype_to_string(self.category), self.ptlocator_size, self.isconstant )
        
        for i in range(self.blobtype_count):
            s += ("   blob %d = %s\n") % (i,self.blobtype_name(i))
                    
        return s       

class ICECacheVersionError(Exception):
    """ICECache version not supported"""
    pass

class ICECacheDataAccessorError(Exception) :
    """ICECache data accessor error"""
    pass

def test():
    r = ICEReader(r'C:\dev\icecache_data\cache50\2.icecache')
    h = r.read_header()
    print h
    a = r.read_attributes_desc()
    for i in a:
        print i
    r.read_attributes_data( )
    print r[ 'PointPosition___' ]

def test2():
    r = ICEReader(r'C:\dev\icecache_data\cache75\pouring_liquid_pointcloud_SimTake1_9.icecache')
    r.load( )
    print r[ 'Size' ]

    
if __name__ == '__main__':
    test2()
