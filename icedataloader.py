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
#from iceviewer import ICEViewer

class ICEDataLoader(QtCore.QThread):
    """ Worker thread for loading ICE cache data. """
    # signal sent data has been loaded
    # string: cache name
    # string: attribute name
    beginCacheDataLoading = QtCore.pyqtSignal( str, str ) 
    endCacheDataLoading = QtCore.pyqtSignal( str, str ) 

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
                    self.beginCacheDataLoading.emit( item.text(0), attribitem.text(1) )
                    self.__load_attribute_data__( attribitem, cacheindex )
                    self.endCacheDataLoading.emit( item.text(0), attribitem.text(1) )            
        elif item.text(0) == 'Attribute':
            # load this attribute data
            cacheitem = item.parent()
            cacheindex = int( cacheitem.text(0).split(' ')[1] )
            self.beginCacheDataLoading.emit( cacheitem.text(0), item.text(1) )
            self.__load_attribute_data__( item, cacheindex )
            self.endCacheDataLoading.emit( cacheitem.text(0), item.text(1) )            

    def __load_attribute_data__( self, item, cacheindex ):
            values = []
            try:
                values = self.viewer.get_data( item.text(1), cacheindex )
            except:
                pass

            nCount = item.childCount()
            dataitem = item.child( nCount -1 )
            for i,val in enumerate(values):
                value = QtGui.QTreeWidgetItem( dataitem )
                value.setText( 0, str(i) )
                value.setText( 1, str(val) )        
            
    def run(self):
        """ Called by the python when the thread has started. """
        
        done = False
        while not self.exiting and not done:            
            self.__load_data__( )
            done = True
