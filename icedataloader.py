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
        self.treewidget = None
        self.viewer = None
        
    def __del__(self):    
        self.exiting = True
        self.wait()

    def load( self, treewidget, viewer ):    
        """ start loading the icecache data """
        self.treewidget = treewidget
        self.viewer = viewer
        
        # kick-off thread
        self.start()

    def __load_data__(self):
        item = self.treewidget.currentItem() 
        
        if item.parent() == None:
            # top level item: load all attribute data            
            cacheindex = int( item.text(0).split(' ')[1] )
            for i in range(item.childCount()):
                attribitem = item.child(i)
                if attribitem.text(0) == 'Attribute':
                    self.__load_attribute_data__( item.text(0), attribitem, cacheindex )
        elif item.text(0) == 'Attribute':
            # load this attribute data
            cacheitem = item.parent()
            cacheindex = int( cacheitem.text(0).split(' ')[1] )
            #self.beginCacheDataLoading.emit( cacheitem.text(0), item.text(1) )
            self.__load_attribute_data__( cacheitem.text(0), item, cacheindex )
            #self.endCacheDataLoading.emit( cacheitem.text(0), item.text(1) )            

    def __load_attribute_data__( self, cache_name, attrib_item, cacheindex ):
            values = []
            try:
                values = self.viewer.get_data( attrib_item.text(1), cacheindex )
            except:
                pass

            self.beginCacheDataLoading.emit( cache_name, attrib_item.text(1), len(values) )

            nCount = attrib_item.childCount()
            dataitem = attrib_item.child( nCount -1 )
            
            for i,val in enumerate(values):
                self.cacheDataLoaded.emit( )
                value = QtGui.QTreeWidgetItem( dataitem )
                value.setText( 0, str(i) )
                # use numpy array string conversion
                value.setText( 1, numpy.array_str(val,precision=6) )        
            
            self.endCacheDataLoading.emit( )            

            
    def run(self):
        """ Called by the python when the thread has started. """
        
        done = False
        while not self.exiting and not done:            
            self.__load_data__( )
            done = True
