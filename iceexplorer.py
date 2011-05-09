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

from iceviewer import ICEViewer
from icereader import ICEReader
from icereader_util import get_files_from_cache_folder
from iceexporter import ICEExporter
from icedataloader import ICEDataLoader
from playback import PlaybackWidget
from consts import CONSTS
from icereader_util import *
from h5reader import H5Reader
from preferences import *

import sys

# (major,minor,micro,label,serial)
__version__ = (1, 0, 0, 'beta', 0)
__author__ = 'mab'

class ICECacheExplorerWindow(QtGui.QMainWindow):
    """ This is the main window for ICE Explorer """
    
    # Supported I/O jobs
    LOAD = 0
    EXPORT = 1
    def __init__(self):
        super(ICECacheExplorerWindow, self).__init__()

        self.setStyleSheet(CONSTS.SS_BACKGROUND)

        self.setWindowTitle("ICE Explorer")
        self.setWindowIcon(QtGui.QIcon('./resources/icex.png'))

        self._create_statusbar()

        self.prefs = ICEPreferences(self)

        # setup the OGL window
        self.viewer = ICEViewer(self)
        self.viewer.cacheLoaded.connect(self._on_cache_loaded)
        self.viewer.beginCacheLoading.connect(self._on_begin_cache_loading)
        self.viewer.endCacheLoading.connect(self._on_end_cache_loading)        
        self.setCentralWidget(self.viewer)
        
        # create object responsible for exporting attributes in the browser
        self.exporter = ICEExporter( self ) 
        self.exporter.cacheExporting.connect(self._on_cache_exporting)
        self.exporter.beginCacheExporting.connect(self._on_begin_cache_exporting)
        self.exporter.endCacheExporting.connect(self._on_end_cache_exporting)

        #self.export_dialog = ICEExporterDialog( self.exporter, self )
        
        # create object responsible for loading attributes data in the browser
        self.data_loader = ICEDataLoader(self)        
        self.data_loader.cacheDataLoaded.connect(self._on_cache_data_loaded)
        self.data_loader.beginCacheDataLoading.connect(self._on_begin_cache_data_loading)
        self.data_loader.endCacheDataLoading.connect(self._on_end_cache_data_loading)
        
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._create_dock_windows()
                
        self.current_job = None
        self._cache_files = []
                
    def _load_cache_folder(self):
        """ Load cache folder from a directory dialog """
        self.statusBar().clearMessage()
        
        fileDialog = QtGui.QFileDialog(self, caption="Select ICECache Folder To Load", directory=".")
        fileDialog.setFileMode(QtGui.QFileDialog.DirectoryOnly)
        fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        fileDialog.setOptions(QtGui.QFileDialog.ShowDirsOnly)
        if not fileDialog.exec_():
            return
                
        self.current_job = self.LOAD
        self.viewer.load_files_from_folder(fileDialog.directory().absolutePath())                
        
    def _load_cache(self):
        """ Load cache file from a file dialog """
        self.statusBar().clearMessage()
        
        fileDialog = QtGui.QFileDialog(self, caption="Select ICECache File(s) To Load", directory=".", filter="ICECACHE (*.icecache *.sih5)")
        fileDialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
        fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        if not fileDialog.exec_():
            return
        
        self.viewer.load_files(fileDialog.selectedFiles())

    def _export_to_text(self):
        """ Select folder cache and export cache files to text """
        self.exporter.folder_dialog.open( CONSTS.TEXT_FMT )

    def _export_to_sih5(self):
        """ Select folder cache and export cache files to SIH5"""
        self.exporter.folder_dialog.open( CONSTS.SIH5_FMT )
    
    def _export_all_to_text(self):
        """ Export all cache files to text """
        self.statusBar().clearMessage()
        self.exporter.file_dialog.open( self._cache_files, CONSTS.TEXT_FMT )
        
    def _export_all_to_sih5(self):
        """ Export all cache files to SIH5 """
        self.statusBar().clearMessage()
        self.exporter.file_dialog.open( self._cache_files, CONSTS.SIH5_FMT )
                
    def preferences(self):
        self.prefs.exec_()

    def close(self):
        sys.exit()

    # Internals

    # slots for the export job
    def _on_begin_cache_exporting(self, num ):
        self.current_job = self.EXPORT
        self.cancel_current_job_act.setDisabled (False)
        self._start_progressbar(num,'Exporting...')

    def _on_cache_exporting(self, export_file):
        self._update_progressbar()

    def _on_end_cache_exporting(self):
        # and we are done
        self.current_job = None
        self.cancel_current_job_act.setDisabled(True)
        self._stop_progressbar()

    # slots for the cache data load job
    def _on_begin_cache_data_loading(self, cache_attrib, num ):
        self._start_progressbar( num, 'Loading data: %s' % (cache_attrib) )

    def _on_cache_data_loaded(self ):
        self._update_progressbar()

    def _on_end_cache_data_loading(self):
        self._stop_progressbar()

    # slots for the cache load job
    def _on_begin_cache_loading(self, count, start, end ):
        self.current_job = self.LOAD
        self.treeWidget.clear()
        self._cache_files = []
        self.cancel_current_job_act.setDisabled(False)
        self._start_progressbar( count, 'Loading Cache Files ...'  )
                
    def _on_end_cache_loading(self, count, start, end ):
        self.current_job = None
        self.cancel_current_job_act.setDisabled(True)
        self._stop_progressbar()

    def _on_cache_loaded(self, cacheindex, filename):
        """update the browser when a cache has finished loading"""
        if cacheindex == None:
            self.statusBar().showMessage( 'Error - invalid file: %s' % filename )
            return

        self._update_progressbar()

        self._cache_files.append( filename )
        
        # Creates browser top level items only, rest will be filled when items get expanded
        # cache item
        itemcache = QtGui.QTreeWidgetItem(self.treeWidget)
        itemcache.setText(0, 'Cache %d' % (cacheindex))
        indexVar = QtCore.QVariant(cacheindex)
        itemcache.setData(0, QtCore.Qt.UserRole, indexVar)
        self.treeWidget.addTopLevelItem(itemcache)
        
        # header item
        headeritem = QtGui.QTreeWidgetItem(itemcache)        
        headeritem.setText(0, 'Header')
        headeritem.setText(1, "ICECACHE")
                
    def _cancel_current_job(self):
        """ cancel the current executing I/O job """
        if self.current_job == self.LOAD:
            self.viewer.stop_loading()
        elif self.current_job == self.EXPORT:
            self.exporter.cancel()

    def _create_actions(self):
        """ All actions required by the GUI components """
        self.load_cache_folder_act = QtGui.QAction(QtGui.QIcon(r'./resources/load-cache-folder.png'), "&Load Cache Folder...", self, statusTip="Load Cache Folder", triggered=self._load_cache_folder)
        self.load_cache_act = QtGui.QAction(QtGui.QIcon(r'./resources/load-cache-file.png'), "Load Cache &File(s)...", self, statusTip="Load Cache File(s)", triggered=self._load_cache)
        self.export_all_caches_to_text_act = QtGui.QAction(QtGui.QIcon(r'./resources/export-cache.png'), "Export Caches to &Text", self, statusTip="Export Caches To Text", triggered=self._export_all_to_text)
        self.export_all_caches_to_sih5_act = QtGui.QAction(QtGui.QIcon(r'./resources/export-cache.png'), "Export Caches to &SIH5", self, statusTip="Export Caches To SIH5", triggered=self._export_all_to_sih5)
        self.export_caches_to_text_act = QtGui.QAction(QtGui.QIcon(r'./resources/export-cache-folder.png'), "Export Folder to &Text", self, statusTip="Export Folder To Text", triggered=self._export_to_text)
        self.export_caches_to_sih5_act = QtGui.QAction(QtGui.QIcon(r'./resources/export-cache-folder.png'), "Export Folder to &SIH5", self, statusTip="Export Folder To SIH5", triggered=self._export_to_sih5)
        self.export_selected_cache_to_text_act = QtGui.QAction(QtGui.QIcon(r'./resources/export-cache.png'), "Export Selected Cache To &Text", self, statusTip="Export To Text")
        self.export_selected_cache_to_sih5_act = QtGui.QAction(QtGui.QIcon(r'./resources/export-cache.png'), "Export Selected Cache To &SIH5", self, statusTip="Export To SIH5")
        self.cancel_current_job_act = QtGui.QAction(QtGui.QIcon(r'./resources/cancel_loading.png'), "Cancel", self, statusTip="Cancel", triggered=self._cancel_current_job)
        self.cancel_current_job_act.setDisabled(True)
        
        self.prefs_act = QtGui.QAction(QtGui.QIcon(r'./resources/preferences.png'), "&Preferences...", self, statusTip="ICE Explorer Preferences", triggered=self.preferences)
        self.quit_act = QtGui.QAction("&Quit", self, shortcut="Ctrl+Q", statusTip="Quit ICE Explorer", triggered=self.close)
        self.about_act = QtGui.QAction("&About", self, statusTip="Show About Dialog", triggered=self.about)

        self.show_pers_act = QtGui.QAction(QtGui.QIcon(r'./resources/perspective.png'), "&Perspective", self, statusTip="Show Perspective View", triggered=self.viewer.perspective_view)
        self.show_top_act = QtGui.QAction(QtGui.QIcon(r'./resources/top.png'), "&Top", self, statusTip="Show Top View", triggered=self.viewer.top_view)
        self.show_front_act = QtGui.QAction(QtGui.QIcon(r'./resources/front.png'), "&Front", self, statusTip="Show Front View", triggered=self.viewer.front_view)
        self.show_right_act = QtGui.QAction(QtGui.QIcon(r'./resources/right.png'), "&Right", self, statusTip="Show Right View", triggered=self.viewer.right_view)

        self.zoom_tool_act = QtGui.QAction(QtGui.QIcon(r'./resources/zoom.png'), "&Zoom", self, statusTip="Zoom Tool", triggered=self.viewer.zoom_tool)
        self.orbit_tool_act = QtGui.QAction(QtGui.QIcon(r'./resources/orbit.png'), "&Orbit", self, statusTip="Orbit Tool", triggered=self.viewer.orbit_tool)
        self.pan_tool_act = QtGui.QAction(QtGui.QIcon(r'./resources/pan.png'), "&Pan", self, statusTip="Pan Tool", triggered=self.viewer.pan_tool)

    def _create_menus(self): 
        self.menuBar().setStyleSheet(CONSTS.SS_MENUBAR)
        
        self.fileMenu = self.menuBar().addMenu("&File")        
        self.fileMenu.setStyleSheet(CONSTS.SS_MENU)
 
        self.fileMenu.addAction(self.load_cache_folder_act)
        self.fileMenu.addAction(self.load_cache_act)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.export_caches_to_text_act)
        self.fileMenu.addAction(self.export_caches_to_sih5_act)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.export_all_caches_to_text_act)
        self.fileMenu.addAction(self.export_all_caches_to_sih5_act)
        self.fileMenu.addAction(self.cancel_current_job_act)
        self.fileMenu.addSeparator()        
        self.fileMenu.addAction(self.cancel_current_job_act)
        self.fileMenu.addAction(self.quit_act)

        self.editMenu = self.menuBar().addMenu("&Edit")
        self.editMenu.setStyleSheet(CONSTS.SS_MENU)
        self.editMenu.addAction(self.prefs_act)
        
        self.viewMenu = self.menuBar().addMenu("&View")
        self.viewMenu.setStyleSheet(CONSTS.SS_MENU)

        self.helpMenu = self.menuBar().addMenu("&Help")
        self.helpMenu.addAction(self.about_act)
        self.helpMenu.setStyleSheet(CONSTS.SS_MENU)

    def _create_toolbars(self):
        self.fileToolBar = QtGui.QToolBar( "File" )
        self.fileToolBar.addAction(self.load_cache_folder_act)
        self.fileToolBar.addAction(self.load_cache_act)
        self.fileToolBar.addSeparator()
        self.fileToolBar.addAction(self.cancel_current_job_act)
        self.addToolBar( QtCore.Qt.LeftToolBarArea, self.fileToolBar )
        
        self.toolsToolBar = QtGui.QToolBar( "Tools" )        
        self.toolsToolBar.addAction(self.orbit_tool_act)
        self.toolsToolBar.addAction(self.pan_tool_act)
        self.toolsToolBar.addAction(self.zoom_tool_act)
        self.addToolBar( QtCore.Qt.LeftToolBarArea, self.toolsToolBar )

        self.viewToolBar = QtGui.QToolBar( "Views" )                
        self.viewToolBar.addAction(self.show_pers_act)
        self.viewToolBar.addAction(self.show_top_act)
        self.viewToolBar.addAction(self.show_front_act)
        self.viewToolBar.addAction(self.show_right_act)
        self.addToolBar( QtCore.Qt.LeftToolBarArea, self.viewToolBar )

    def _create_statusbar(self):
        """ The status bar contains a temporary message (left area ), a progress bar (left area) and a permanent msg on the right. """
        self.pbar = QtGui.QProgressBar(self.statusBar())
        self.pbar.setTextVisible(False)
        self.pbar.hide()        
        self.middle_msg = QtGui.QLabel(self.statusBar())
        self.right_msg = QtGui.QLabel(self.statusBar())

        self.statusBar().addWidget(self.pbar,2)
        self.statusBar().addWidget(self.middle_msg,1)
        self.statusBar().addPermanentWidget(self.right_msg)
        self.statusBar().showMessage("Ready")

    def _create_dock_windows(self):
        """ Creates and organizes all dockable windows"""
        
        # Cache file browser 
        dock = QtGui.QDockWidget("Browser", self)
        dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.treeWidget = QtGui.QTreeWidget(dock)
        self.treeWidget.itemExpanded.connect( self._handle_item_expanded )
        self.treeWidget.setObjectName('ICECacheInspectorWidget')
        self.treeWidget.setColumnCount(2)
        self.treeWidget.headerItem().setText(0, 'Item')
        self.treeWidget.headerItem().setText(1, 'Value')
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self._handle_browser_contextmenu)
        self.treeWidget.setStyleSheet(CONSTS.SS_BACKGROUND)
        
        # ... browser context menus
        self._browser_contextmenu = QtGui.QMenu(self)
        self._browser_contextmenu.setStyleSheet(CONSTS.SS_MENU)
        self._browser_contextmenu.addAction(self.export_selected_cache_to_text_act)
        self._browser_contextmenu.addAction(self.export_selected_cache_to_sih5_act)
        self.attribute_contextmenu = QtGui.QMenu(self)
        self.attribute_contextmenu.setStyleSheet(CONSTS.SS_MENU)
        dock.setWidget(self.treeWidget)        
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

        # Playback widget
        dock = QtGui.QDockWidget("Play Back", self)
        dock.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea)        
        self.playback = PlaybackWidget(self.viewer, dock)                
        dock.setWidget(self.playback)            
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        self.viewMenu.addAction(dock.toggleViewAction())

    def _handle_item_expanded( self, item ):
        """ Fill items data when the node gets expanded """
        var = item.data(0, QtCore.Qt.UserRole)
        if var == None:
            # nothing to do
            return
        
        #Fill this item with cache attributes
        (cacheindex,flag) = var.toInt()
        h5cache = self.viewer.cache[ cacheindex ]
        
        if item.text(0) == 'Data':
            self.data_loader.load(h5cache,item)                  
            return

        #done with the user data
        item.setData(0, QtCore.Qt.UserRole, None)

        reader = H5Reader( h5cache )
        reader.load()
        
        # Cache
        #    > Header
        #         <header items>
        headeritem = item.child(0)
        headeritem.setText(0, 'Header')
        headeritem.setText(1, reader.header['name'])
        
        version = QtGui.QTreeWidgetItem(headeritem)
        type = QtGui.QTreeWidgetItem(headeritem)
        edge_count = QtGui.QTreeWidgetItem(headeritem)
        particle_count = QtGui.QTreeWidgetItem(headeritem)
        polygon_count = QtGui.QTreeWidgetItem(headeritem)
        sample_count = QtGui.QTreeWidgetItem(headeritem)
        blob_count = QtGui.QTreeWidgetItem(headeritem)
        attribute_count = QtGui.QTreeWidgetItem(headeritem)

        version.setText(0, 'Version')
        version.setText(1, str(reader.header['version']))
        type.setText(0, 'Type')
        type.setText(1, objtype_to_string(reader.header['type']))
        particle_count.setText(0, 'Particle Count')
        particle_count.setText(1, str(reader.header['particle_count']))
        edge_count.setText(0, 'Edge Count')
        edge_count.setText(1, str(reader.header['edge_count']))
        polygon_count.setText(0, 'Polygon Count')
        polygon_count.setText(1, str(reader.header['polygon_count']))
        sample_count.setText(0, 'Sample Count')
        sample_count.setText(1, str(reader.header['sample_count']))
        blob_count.setText(0, 'Blob Count')
        blob_count.setText(1, str(reader.header['blob_count']))
        attribute_count.setText(0, 'Attribute Count')
        attribute_count.setText(1, str(reader.header['attribute_count']))

        # attribute items
        # Cache
        #    > Header
        #         <header items>
        #    > Attribute <name>
        #         <attribute items>        

        for attrib in reader.attributes:
            attribitem = QtGui.QTreeWidgetItem(item)
            attribitem.setText(0, 'Attribute')
            attribitem.setText(1, attrib['name'] )

            # attribute description
            datatype = QtGui.QTreeWidgetItem(attribitem)
            structtype = QtGui.QTreeWidgetItem(attribitem)
            contexttype = QtGui.QTreeWidgetItem(attribitem)
            objid = QtGui.QTreeWidgetItem(attribitem)
            category = QtGui.QTreeWidgetItem(attribitem)
            ptlocator_size = QtGui.QTreeWidgetItem(attribitem)
            blobtype_count = QtGui.QTreeWidgetItem(attribitem)
            blobtype_names = QtGui.QTreeWidgetItem(attribitem)
            isconstant = QtGui.QTreeWidgetItem(attribitem)
            dataitem = QtGui.QTreeWidgetItem(attribitem)

            datatype.setText(0, 'Data Type')
            datatype.setText(1, datatype_to_string(attrib['datatype']))
            structtype.setText(0, 'Structure Type')
            structtype.setText(1, structtype_to_string(attrib['structtype']))
            contexttype.setText(0, 'Context Type')
            contexttype.setText(1, contexttype_to_string(attrib['contexttype']))
            objid.setText(0, 'Object ID')
            objid.setText(1, str(attrib['objid']))
            category.setText(0, 'Category')
            category.setText(1, categorytype_to_string(attrib['category']))
            ptlocator_size.setText(0, 'PointLocator Size')
            ptlocator_size.setText(1, str(attrib['ptlocator_size']))
            blobtype_count.setText(0, 'Blob Type Count')
            blobtype_count.setText(1, str(attrib['blobtype_count']))
            blobtype_names.setText(0, 'Blob Type Name')
            blobtype_names.setText(1, str(attrib['blobtype_names']))
            # will be filled when the data gets loaded by the user
            isconstant.setText(0, 'Constant Data')            
            isconstant.setText(1, '')
            
            # attribute data items, empty for now
            # Cache
            #    > Header 
            #         <header items>
            #    > Attribute <name>
            #         <attribute items>        
            #         > Data
            #              <values>
            dataitem.setText(0, 'Data')
            var = QtCore.QVariant(cacheindex)
            dataitem.setData(0, QtCore.Qt.UserRole, var )            

            # add dummy value so data item can get filled with values when it get expanded
            emptyvalue = QtGui.QTreeWidgetItem( dataitem )
            emptyvalue.setText( 0, '' )

    def _handle_browser_contextmenu(self, point):
        """ Context menus for  exporting individual cache files"""
        item = self.treeWidget.currentItem() 
        
        # show browser context menu on the widget
        if item.parent() != None:
            # context menu supported on the top level item only
            return
        
        action = self._browser_contextmenu.exec_(self.treeWidget.mapToGlobal(point))
        var = item.data(0, QtCore.Qt.UserRole)
        (cache_index,flag) = var.toInt()
        fmt=None
        if action == self.export_selected_cache_to_text_act:
            fmt = CONSTS.TEXT_FMT
        elif action == self.export_selected_cache_to_sih5_act:                
            fmt = CONSTS.SIH5_FMT
        else:
            return
        
        h5cache = self.viewer.cache[ cache_index ]
        self.exporter.export_files( [h5cache.filename], self.prefs.export_folder, fmt)                

    # Progress bar helpers
    def _start_progressbar(self,num,msg=''):        
        self.pbar.show()
        self.pbar.setRange(0, num)
        self.pbar.setValue(1)
        self.middle_msg.setText( msg )

    def _update_progressbar(self):        
        self.pbar.setValue(self.pbar.value() + 1)        

    def _stop_progressbar(self):        
        self.pbar.hide()
        self.pbar.reset()
        self.middle_msg.clear( )

    def about(self):
        msg = "<b>ICE Explorer</b> Copyright (C) 2010  M.A.Belzile <br>"\
            "A tool for viewing and browsing ICE cache data.<br>"\
            "Version %d.%d.%d %s %d<br><br>"\
            "This program comes with ABSOLUTELY NO WARRANTY; for details see the GNU General Public License."\
            "This is free software, and you are welcome to redistribute it under certain conditions; see the GNU General Public License for details."
        QtGui.QMessageBox.about(self, "About ICE Explorer", msg % (__version__[0], __version__[1], __version__[2], __version__[3], __version__[4]))
