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

from PyQt4 import QtCore, QtGui
import numpy
from icereader import ICEReader

class ICEDataLoader(QtCore.QThread):
    """ Worker thread for loading ICE cache data. """
    # signals
    # string: cache name
    # string: attribute name
    # int: num values
    beginCacheDataLoading = QtCore.pyqtSignal( str, str, int ) 
    endCacheDataLoading = QtCore.pyqtSignal( ) 
    cacheDataLoaded = QtCore.pyqtSignal( ) 

    def __init__(self, parent = None):
        super(ICEDataLoader,self).__init__(parent)
        self.exiting = False
        self.treeitem = None
        
    def __del__(self):    
        self.exiting = True
        self.wait()

    def load( self, treeitem ):    
        """ start loading the icecache data """
        self.treeitem = treeitem
        
        # kick-off thread
        self.start()

    def _load_data(self):
        item = self.treeitem
            
        if item.text(0) == 'Data':
            # load this data
            var = item.data(0, QtCore.Qt.UserRole)
            if var == None:
                raise Exception('Unexpected data item ')
                return 
            
            filename,cache_name = var.toStringList()
 
            attrib_name  = item.parent().text(1)

            reader = ICEReader( filename )
            reader.load( )
            
            values = []
            if attrib_name in reader._data:
                values = reader[ attrib_name ]
                #update <attrib_name>.isconstant value
                isconst_item = item.parent().child(8)
                isconst_item.setText(1, str(reader.find_attribute( attrib_name ).isconstant) )
                        
            item.takeChild(0)
            self.beginCacheDataLoading.emit( cache_name, item.parent().text(1), len(values) )

            for i,val in enumerate(values):
                value = QtGui.QTreeWidgetItem( item )
                value.setText( 0, str(i) )
                # use numpy array string conversion
                value.setText( 1, numpy.array_str(val,precision=6) )        
                self.cacheDataLoaded.emit( )

            item.setData(0,QtCore.Qt.UserRole,None)
            self.endCacheDataLoading.emit( )                    
    
    def _load_attribute_data( self, cache_name, attrib_item, cacheindex ):
            values = []
            try:
                # get the attribute data from the viewer
                values = self.viewer.get_data( attrib_item.text(1), cacheindex )
            except:
                pass

            self.beginCacheDataLoading.emit( cache_name, attrib_item.text(1), len(values) )

            nCount = attrib_item.childCount()
            dataitem = attrib_item.child( nCount -1 )
            for i,val in enumerate(values):
                value = QtGui.QTreeWidgetItem( dataitem )
                value.setText( 0, str(i) )
                # use numpy array string conversion
                value.setText( 1, numpy.array_str(val,precision=6) )        
                self.cacheDataLoaded.emit( )
            
            self.endCacheDataLoading.emit( )

    def run(self):
        """ Called by the python when the thread has started. """
        
        done = False
        while not self.exiting and not done:            
            self._load_data( )
            done = True
