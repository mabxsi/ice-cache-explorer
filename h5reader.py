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
from consts import CONSTS
from icereader_util import *
import shutil

try:
    import h5py as h5
except:
    print "ERROR: h5py not installed properly."
    sys.exit()

class H5Reader(object):    
    """ H5 file format reader """
    
    def __init__(self,obj):
        """ init reader with H5 file or object """
        self._filename = None
        self._file = None

        if isinstance(obj, h5.highlevel.File):
            self._file = obj
        else:
            self._filename = obj

        self._header = None
        self._attributes = None        
        
        try:
            if self._file == None:
                self._file = h5.File( self._filename, 'r' )
        except:
            raise Exception('Error - Invalid file: %s' % self._filename )
                               
    def __del__(self):
        self._header = None
        self._attributes = None
        if self._filename != None and self._file:
            self._file.close()

    def __getitem__(self,arg):
        return self._attributes[arg].data
    
    @property
    def filename(self):
        return self._filename

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
            self._read_attributes()
        except:
            raise Exception('H5Reader - load error')
        
    def find_attribute( self, name ):
        for a in self._attributes:
            if a.name == name:
                return a
        return None
                    
    def close(self):
        self._file.close()

    def export(self, destination_folder, fmt, force = True ):                
        if self._file == None:
            raise Exception('H5Reader - No file to export')
            return

        if fmt!=CONSTS.SIH5_FMT and fmt!=CONSTS.TEXT_FMT:
            raise Exception('Error export format not supported')
            return

        ext = None
        if fmt != CONSTS.SIH5_FMT:
            ext = EXT[ fmt ]
            
        self._export_filename = get_export_file_path( destination_folder, self._file.filename, ext )

        if force == False and os.path.isfile( self._export_filename ):
            # reuse existing file
            return
        
        if fmt==CONSTS.SIH5_FMT:
            # just copy the file to destination
            try:
                shutil.copyfile( self._file.filename, self._export_filename )
            except:
                raise Exception('H5Reader - Error copying: %s' % self._export_filename )
            return
        
        try:
            # load data 
            self.load( )
        except:
            raise Exception('H5Reader - load error')
            return
        
        try:
            if fmt == CONSTS.TEXT_FMT:
                to_ascii( self._export_filename, self )
        except:
            raise Exception('H5Reader - ICECache export failed: %s' % self._export_filename )
        
    # Internals
    def _read_header(self):        
        """ Read header section -> /HEADER. """
        self._header = None
        try:
            h = self._file['/HEADER']
            self._header = Header(h)            
        except:
            raise Exception('H5Reader - Error reading header section')        
        return self._header

    def _read_attributes(self):
        """ Read attribute section -> /HEADER/ATTRIBS/* """
        try:
            attribs = self._file['/ATTRIBS']
        
            self._attributes = []
            for a in attribs:
                obj = self._file[ '/ATTRIBS/%s' % a ]
                self._attributes.append( Attribute(obj,a) )
        except:
            raise Exception('H5Reader - Error reading attribute sections')
        
        return self._attributes

def is_valid_file( cachefile ):
    return cachefile.endswith('.sih5') or cachefile.endswith('.hdf5')

class Header(object):
    """ H5 Header object """
    def __init__(self,h5_header):
        self.h5_header = h5_header

    def __getitem__( self, arg ):
        """ return attribute by name """
        return self.h5_header.attrs[ arg ]

    def __iter__(self):
        """ Iterate over the names of attributes. """
        for name in self.h5_header.attrs:
            yield name

    def __contains__(self, name):
        """ Test if a member name exists """
        return name in self.h5_header.attrs
    
    def __str__(self):
        s = '[Header info]\n'
        for a in self.h5_header.attrs:
            s += '%s = %s\n' % ( a, str(self.h5_header.attrs[a]) )
        return  s

class Attribute(object):
    """ H5 Attribute object """
    def __init__(self,h5_attrib, name):
        self.h5_attrib = h5_attrib
        self.name = name

    def __getitem__( self, arg ):
        """ return attribute by name """
        return self.h5_attrib.attrs[ arg ]

    def __iter__(self):
        """ Iterate over the names of attributes. """
        for name in self.h5_attrib.attrs:
            yield name

    def __contains__(self, name):
        """ Test if a member name exists """
        return name in self.h5_attrib.attrs

    @property
    def data(self):
        try:
            return self.h5_attrib['Data'][:]
        except:
            return []
        
    def __str__(self):
        return attribs_to_str( self.h5_attrib.attrs )

def test1(): 
    #file = r'C:\dev\icecache_data\test_14.sih5'
    file = r'C:\dev\icecache_data\cache10\.sih5\1.icecache.sih5'    
    r = H5Reader( file )
    r.load( )
    for ha in r.header:
        print ha, r.header[ha]

    for attrib in r.attributes:
        for name in attrib:
            val = attrib[name]
            print name, val
        print len(attrib.data)
        print attrib.data
    
    r.close()
    
    file = r'C:\dev\icecache_data\test_16.sih5'
    obj = h5.File( file, 'r' )
    r = H5Reader( obj )
    
    r.load( )
    for ha in r.header:
        print ha, r.header[ha]

    for attrib in r.attributes:
        print str(attrib)
    
    print str(r.header)
    r.close()

def test2(): 
    #file = r'C:\dev\icecache_data\test_14.sih5'
    file = r'C:\dev\icecache_data\cache10\.sih5\1.icecache.sih5'
    r = H5Reader( file )
    folder = r'c:\temp'
    r.export( folder, fmt=CONSTS.TEXT_FMT, force=True )

    file = r'C:\dev\icecache_data\test_16.sih5'
    r = H5Reader( file )
    folder = r'C:\temp'
    r.export( folder, fmt=CONSTS.SIH5_FMT, force=True )

if __name__ == '__main__':
    test1()
    test2()
