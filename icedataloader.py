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

from PyQt4 import QtCore, QtGui
import numpy
from h5reader import H5Reader

class ICEDataLoader(QtCore.QThread):
    """ Worker thread for loading ICE cache data. """
    # signals
    # string: attribute name
    # int: num values
    beginCacheDataLoading = QtCore.pyqtSignal( str, int ) 
    endCacheDataLoading = QtCore.pyqtSignal( ) 
    cacheDataLoaded = QtCore.pyqtSignal( ) 

    def __init__(self, parent = None):
        super(ICEDataLoader,self).__init__(parent)
        self.exiting = False
        self.treeitem = None        
        self.h5_obj = None
        
    def __del__(self):    
        self.exiting = True
        self.wait()

    def load( self, loader, treeitem ):    
        """ start loading the icecache data """
        self.treeitem = treeitem
        self.h5_obj = loader
        
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
            
            #filename,cache_name = var.toStringList() 
            attrib_name  = item.parent().text(1)

            reader = H5Reader( self.h5_obj )
            
            try:
                reader.load( )
            except:
                raise Exception('Error loading data')
                return
            
            attrib = reader.find_attribute( attrib_name )
            
            if attrib == None:
                raise Exception('Unexpected attribute')
                return 
                       
            values = attrib.data[:]
            #update <attrib_name>.isconstant value
            isconst_item = item.parent().child(8)
            isconst_item.setText(1, str(attrib['isconstant']) )
                        
            item.takeChild(0)
            self.beginCacheDataLoading.emit( attrib_name, len(values) )

            for i,val in enumerate(values):
                value = QtGui.QTreeWidgetItem( item )
                value.setText( 0, str(i) )
                # use numpy array string conversion
                value.setText( 1, numpy.array_str(val,precision=6) )        
                self.cacheDataLoaded.emit( )

            item.setData(0,QtCore.Qt.UserRole,None)
            self.endCacheDataLoading.emit( )                    
    
    def run(self):
        """ Called by the python when the thread has started. """
        
        done = False
        while not self.exiting and not done:            
            self._load_data( )
            done = True
