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
from consts import CONSTS
from icereader_util import *

try:
    import numpy 
except:
    print "ERROR: numpy not installed properly."
    sys.exit()

try:
    import h5py as h5
except:
    print "ERROR: h5py not installed properly."
    h5 = None

"""
import gc
 gc.set_debug(gc.DEBUG_LEAK)
"""

class ICEReader(object):    
    """ ICE cache reader/exporter """
    
    def __init__(self,filename):
        """ open file and store the file pointer """
        self._filename = filename
        self._header = None
        self._attributes = None
        self._data = {}
        self._export_filename = None
        
        file = None
        try:
            file = gzip.open( self._filename, 'rb+' )
        except:
            raise Exception('Error - Invalid file: %s' % filename )
                               
        self.handler = ICECacheFileHandler( file )

    def __del__(self):
        self._header = None
        self._attributes = None
        self._data = {}
        self.handler = None

    def __getitem__( self, arg ):
        """ return data buffer by name """
        return self._data[ arg ]

    @property
    def filename(self):
        return self._filename

    @property
    def export_filename(self):
        return self._export_filename

    @property
    def header(self):
        return self._header

    @property
    def attributes(self):
        return self._attributes

    def load( self ):
        """ load the underlying cache file """
        try:
            self._read_header()
            self._read_attributes_desc()
            self._read_attributes_data()
            self.handler.file.flush()
        except ICECacheVersionError:
            print 'Error - ICE Cache version not supported'
        
        if self._header == None:
            raise ICECacheDataReadError

    def find_attribute( self, name ):
        for a in self._attributes:
            if a.name == name:
                return a
        return None
    
    def export(self, destination_folder, fmt=CONSTS.TEXT_FMT, force = True ):                
        if fmt==CONSTS.SIH5_FMT and h5 == None:
            return

        if fmt!=CONSTS.SIH5_FMT and fmt!=CONSTS.TEXT_FMT:
            raise Exception('Error export format not supported')
            return
        
        self._export_filename = get_export_file_path( destination_folder, self._filename,  EXT[ fmt ] )        

        if force == False and os.path.isfile( self._export_filename ):
            # reuse existing file
            return
        
        try:
            # load the requested attributes
            self.load( )
        except:
            raise Exception('Error loading data: %s' % self._export_filename )
            return
        
        try:
            if fmt == CONSTS.TEXT_FMT:
                to_ascii( self._export_filename, self )
            elif fmt == CONSTS.SIH5_FMT:
                to_sih5( self._export_filename, self )
        except:
            pass
            #raise Exception('Error exporting file: %s' % self.filename )
            
    def close(self):
        del self.handler
        self.handler = None
               
    # Internals
    def _read_header(self):        
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
            report_error( 'Error - ICE Cache version not supported', sys.exc_info() )
            return
        
        try:
            self._header.read( self.handler )            
        except:
            report_error( 'self._header', sys.exc_info() )
            raise Exception

        return self._header

    def _read_attributes_desc(self):       
        """ Read all attribute descriptions """
        if self._header == None:
            return None        
        
        self._attributes = []
        for i in range(self._header.attribute_count):            
            attrib = Attribute(self)        
            attrib.read( self.handler )            
            self._attributes.append( attrib )
        
        return self._attributes

    def _read_attributes_data( self ):
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
        self.substeps_count = 0
        
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

    def __getitem__( self, arg ):
        """ return attribute by name """
        return self.__dict__[ arg ]

    def __iter__(self):
        """ Iterate over the names of dictionary. """
        for name in self.__dict__:
            yield name

    def __contains__(self, name):
        """ Test if a member name exists """
        return name in self.__dict__

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
        self.substeps_count = 0

    def read( self, handler ):
        self.name = handler.read_header_name( )
        self.version = handler.read_int( )
        self.type = handler.read_int( )
        self.particle_count = handler.read_int( )
        self.edge_count = handler.read_int( )
        self.polygon_count = handler.read_int( )
        self.sample_count = handler.read_int( )
        self.substeps_count = handler.read_int( )
        self.blob_count = handler.read_int( )
        self.attribute_count = handler.read_int( )

    def __getitem__( self, arg ):
        """ return attribute by name """
        return self.__dict__[ arg ]

    def __iter__(self):
        """ Iterate over the names of dictionary. """
        for name in self.__dict__:
            yield name

    def __contains__(self, name):
        """ Test if a member name exists """
        return name in self.__dict__

    def __str__(self):
        return  ("[Header info]\nname = %s\nversion = %d\ntype = %s\nparticle_count = %d\nedge_count = %d\npolygon_count = %d\nsample_count = %d\nblob_count = %d\nattribute_count = %d\nsubsteps_count = %d\n\n") % ( self.name, self.version, objtype_to_string(self.type), self.particle_count, self.edge_count, self.polygon_count, self.sample_count, self.blob_count, self.attribute_count, self.substeps_count )

class Attribute(object):
    """ ICECache Attribute object """
    def __init__(self,reader):
        self.name = None
        self.datatype = 0
        self.structtype = 0
        self.contexttype = 0
        self.objid = 0
        self.category = 0
        self.ptlocator_size = 0
        self.blobtype_count = 0
        self.blobtype_names = ('')
        self.isconstant = True
        self._reader = reader

    def read( self, handler ):
        self.name = handler.read_name()
        self.datatype = handler.read_int()
        
        if self.datatype == CONSTS.siICENodeDataCustomType:
            self.blobtype_count = handler.read_ulong()            
            attrib.blobtype_names = ()
            for i in range( self.blobtype_count ):
                attrib.blobtype_names.append( handler.read_name() )                

        self.structtype = handler.read_int()
        self.contexttype = handler.read_int()
        self.objid = handler.read_int()
        self.category = handler.read_int()

        if self.datatype == CONSTS.siICENodeDataLocation:
            self.ptlocator_size = handler.read_ulong()

    @property
    def data(self):
        try:
            return self._reader[ self.name ]
        except:
            return []

    def __getitem__( self, arg ):
        """ return attribute by name """
        return self.__dict__[ arg ]

    def __iter__(self):
        """ Iterate over the names of dictionary. """
        for name in self.__dict__:
            yield name

    def __contains__(self, name):
        """ Test if a member name exists """
        return name in self.__dict__
        
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

def test1():
    r = ICEReader(r'C:\dev\icecache_data\14.icecache')
    h = r.read_header()
    print h
    a = r.read_attributes_desc()
    for i in a:
        print i
    r.read_attributes_data( )
    print r[ 'PointPosition___' ]

def test2():
    r = ICEReader(r'C:\dev\icecache_data\16.icecache')
    r.load( )
    try:
        print r[ 'Size' ]
    except:
        try:
            print r[ 'Color___' ]
        except:
            pass

def test3(): 
    r = ICEReader(r'C:\dev\icecache_data\14.icecache')
    folder = r'C:\temp'
    r.export( folder, fmt=CONSTS.SIH5_FMT, force=True )

    r = ICEReader(r'C:\dev\icecache_data\16.icecache')
    folder = r'C:\temp'
    r.export( folder, fmt=CONSTS.TEXT_FMT, force=True )

def test4(): 
    r = ICEReader(r'C:\dev\icecache_data\cache50\15.icecache')
    folder = r'C:\dev\svn\cache_test\.iceexplorer'
    r.load( )
    
    for a in r.header:
        print a, r.header[a]

if __name__ == '__main__':
    #test1()
    test2()
    test3()
    #test4()
