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

from iceviewer import ICEViewer
from icereader import get_files_from_cache_folder
from iceexporter import ICEExporter
from icedataloader import ICEDataLoader
from playback import PlaybackWidget
from consts import CONSTS
from icereader_util import *

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

        self.__create_statusbar__()

        # setup the OGL window
        self.viewer = ICEViewer(self)
        self.viewer.cacheLoaded.connect(self.on_cache_loaded)
        self.viewer.beginCacheLoading.connect(self.on_begin_cache_loading)
        self.viewer.endCacheLoading.connect(self.on_end_cache_loading)        
        self.setCentralWidget(self.viewer)

        # setup the worker threads for exporting and loading attribute data in the browser
        self.exporter_thread = ICEExporter(self)        
        self.exporter_thread.cacheExporting.connect(self.on_cache_exporting)
        self.exporter_thread.beginCacheExporting.connect(self.on_begin_cache_exporting)
        self.exporter_thread.endCacheExporting.connect(self.on_end_cache_exporting)

        self.data_loader_thread = ICEDataLoader(self)        
        self.data_loader_thread.cacheDataLoaded.connect(self.on_cache_data_loaded)
        self.data_loader_thread.beginCacheDataLoading.connect(self.on_begin_cache_data_loading)
        self.data_loader_thread.endCacheDataLoading.connect(self.on_end_cache_data_loading)
        
        self.__create_actions__()
        self.__create_menus__()
        self.__create_toolbars__()
        self.__create_dock_windows__()
                
        self.current_job = None
                
    def load_cache_folder(self):
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
        
    def load_cache(self):
        """ Load cache file from a file dialog """
        self.statusBar().clearMessage()
        
        fileDialog = QtGui.QFileDialog(self, caption="Select ICECache File(s) To Load", directory=".", filter="ICECACHE (*.icecache)")
        fileDialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
        fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        if not fileDialog.exec_():
            return
        
        self.viewer.load_files(fileDialog.selectedFiles())

    def export_cache_folder(self):
        """ Export all cache files from dir to ascii """
        self.statusBar().clearMessage()
        folder = QtGui.QFileDialog.getExistingDirectory(self, "Select ICECache Folder To Export", ".", QtGui.QFileDialog.ShowDirsOnly)
        if not folder:
            return

        self.exporter_thread.export_folder(folder, r'c:\temp', ('Color___', 'Size___'))
        
    def export_cache(self):
        """ Export a selected icecache to ascii """
        self.statusBar().clearMessage()
        fileDialog = QtGui.QFileDialog(self, caption="Select ICECache File(s) To Export", directory=".", filter="ICECACHE (*.icecache)")
        fileDialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
        fileDialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        if not fileDialog.exec_():
            return
        self.exporter_thread.export_files(fileDialog.selectedFiles(), r'c:\temp', ('Color___', 'Size___'))

    def preferences(self):
        pass

    def close(self):
        sys.exit()

    # Internals
    def __load_cache_data__(self):
        """ start worker thread to load the attribute(s) data """
        self.data_loader_thread.load(self.treeWidget, self.viewer)

    # slots for the export job
    def on_begin_cache_exporting(self, num ):
        self.current_job = self.EXPORT
        self.cancel_current_job_act.setDisabled(False)
        self.__start_progressbar__(num,'Exporting...')

    def on_cache_exporting(self, export_file):
        self.__update_progressbar__()

    def on_end_cache_exporting(self):
        # and we are done
        self.current_job = None
        self.cancel_current_job_act.setDisabled(True)
        self.__stop_progressbar__()

    # slots for the cache data load job
    def on_begin_cache_data_loading(self, cache_name, cache_attrib, num ):
        self.__start_progressbar__( num, 'Loading "%s.%s" data ...' % (cache_name, cache_attrib) )

    def on_cache_data_loaded(self ):
        self.__update_progressbar__()

    def on_end_cache_data_loading(self):
        self.__stop_progressbar__()

    # slots for the cache load job
    def on_begin_cache_loading(self, count, start, end ):
        self.current_job = self.LOAD
        self.treeWidget.clear()
        self.cancel_current_job_act.setDisabled(False)
        self.__start_progressbar__( count, 'Loading Cache Files ...'  )
                
    def on_end_cache_loading(self, count, start, end ):
        self.current_job = None
        self.cancel_current_job_act.setDisabled(True)
        self.__stop_progressbar__()

    def on_cache_loaded(self, cacheindex, reader):
        """update the browser when a cache has finished loading"""
        
        if reader.header() == None:
            self.statusBar().showMessage( 'Error - invalid file: %s' % reader.filename() )
            return
            
        self.__update_progressbar__()
                
        # cache item
        itemcache = QtGui.QTreeWidgetItem(self.treeWidget)
        itemcache.setText(0, 'Cache %d' % (cacheindex))
        fnameVar = QtCore.QVariant(reader.filename())
        itemcache.setData(0, QtCore.Qt.UserRole, fnameVar)
        self.treeWidget.addTopLevelItem(itemcache)
        
        # header items
        # Cache
        #    > Header
        #         <header items>
        headeritem = QtGui.QTreeWidgetItem(itemcache)        
        headeritem.setText(0, 'Header')
        headeritem.setText(1, reader.header().name)
        
        version = QtGui.QTreeWidgetItem(headeritem)
        type = QtGui.QTreeWidgetItem(headeritem)
        edge_count = QtGui.QTreeWidgetItem(headeritem)
        particle_count = QtGui.QTreeWidgetItem(headeritem)
        polygon_count = QtGui.QTreeWidgetItem(headeritem)
        sample_count = QtGui.QTreeWidgetItem(headeritem)
        blob_count = QtGui.QTreeWidgetItem(headeritem)
        attribute_count = QtGui.QTreeWidgetItem(headeritem)
        
        version.setText(0, 'Version')
        version.setText(1, str(reader.header().version))
        type.setText(0, 'Type')
        type.setText(1, objtype_to_string(reader.header().type))
        particle_count.setText(0, 'Particle Count')
        particle_count.setText(1, str(reader.header().particle_count))
        edge_count.setText(0, 'Edge Count')
        edge_count.setText(1, str(reader.header().edge_count))
        polygon_count.setText(0, 'Polygon Count')
        polygon_count.setText(1, str(reader.header().polygon_count))
        sample_count.setText(0, 'Sample Count')
        sample_count.setText(1, str(reader.header().sample_count))
        blob_count.setText(0, 'Blob Count')
        blob_count.setText(1, str(reader.header().blob_count))
        attribute_count.setText(0, 'Attribute Count')
        attribute_count.setText(1, str(reader.header().attribute_count))                

        # attribute items
        # Cache
        #    > Header
        #         <header items>
        #    > Attribute <name>
        #         <attribute items>        
                
        for attrib in reader.attributes():
            attribitem = QtGui.QTreeWidgetItem(itemcache)
            attribitem.setText(0, 'Attribute')
            attribitem.setText(1, attrib.name)

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
            datatype.setText(1, datatype_to_string(attrib.datatype))
            structtype.setText(0, 'Structure Type')
            structtype.setText(1, structtype_to_string(attrib.structtype))
            contexttype.setText(0, 'Context Type')
            contexttype.setText(1, contexttype_to_string(attrib.contexttype))
            objid.setText(0, 'Object ID')
            objid.setText(1, str(attrib.objid))
            category.setText(0, 'Category')
            category.setText(1, categorytype_to_string(attrib.category))
            ptlocator_size.setText(0, 'PointLocator Size')
            ptlocator_size.setText(1, str(attrib.ptlocator_size))
            blobtype_count.setText(0, 'Blob Type Count')
            blobtype_count.setText(1, str(attrib.blobtype_count))
            blobtype_names.setText(0, 'Blob Type Name')
            blobtype_names.setText(1, str(attrib.blobtype_names))
            isconstant.setText(0, 'Constant Data')
            isconstant.setText(1, str(attrib.isconstant))

            # attribute data items
            # Cache
            #    > Header
            #         <header items>
            #    > Attribute <name>
            #         <attribute items>        
            #         > Data
            #              <values>
            dataitem.setText(0, 'Data')
            
            # values are displayed through the popup menu
        
    def __cancel_current_job__(self):
        """ cancel the current executing I/O job """
        if self.current_job == self.LOAD:
            self.viewer.stop_loading()
        elif self.current_job == self.EXPORT:
            self.exporter_thread.cancel()

    def __create_actions__(self):
        """ All actions required by the GUI components """
        self.load_cache_folder_act = QtGui.QAction(QtGui.QIcon(r'./resources/load-cache-folder.png'), "&Load Cache Folder...", self, statusTip="Load Cache Folder", triggered=self.load_cache_folder)
        self.load_cache_act = QtGui.QAction(QtGui.QIcon(r'./resources/load-cache-file.png'), "Load Cache &File(s)...", self, statusTip="Load Cache File(s)", triggered=self.load_cache)
        self.load_cache_data_act = QtGui.QAction(QtGui.QIcon(r'./resources/display-data.png'), "&Display Data", self, statusTip="Display Data", triggered=self.__load_cache_data__)
        self.export_cache_act = QtGui.QAction(QtGui.QIcon(r'./resources/export-cache.png'), "Export &Cache File(s)...", self, statusTip="Export Cache File(s)", triggered=self.export_cache)
        self.export_selected_cache_act = QtGui.QAction(QtGui.QIcon(r'./resources/export-cache.png'), "Export &Cache File", self, statusTip="Export Cache")
        self.export_cache_folder_act = QtGui.QAction(QtGui.QIcon(r'./resources/export-cache-folder.png'), "Export &Cache Folder...", self, statusTip="Export Cache Folder", triggered=self.export_cache_folder)
        self.cancel_current_job_act = QtGui.QAction(QtGui.QIcon(r'./resources/cancel_loading.png'), "Cancel", self, statusTip="Cancel", triggered=self.__cancel_current_job__)
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

    def __create_menus__(self): 
        self.menuBar().setStyleSheet(CONSTS.SS_MENUBAR)
        
        self.fileMenu = self.menuBar().addMenu("&File")        
        self.fileMenu.setStyleSheet(CONSTS.SS_MENU)
 
        self.fileMenu.addAction(self.load_cache_act)
        self.fileMenu.addAction(self.load_cache_folder_act)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.export_cache_act)
        self.fileMenu.addAction(self.export_cache_folder_act)
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

    def __create_toolbars__(self):
        self.fileToolBar = QtGui.QToolBar( "File" )
        self.fileToolBar.addAction(self.load_cache_folder_act)
        self.fileToolBar.addAction(self.load_cache_act)
        self.fileToolBar.addSeparator()
        self.fileToolBar.addAction(self.export_cache_folder_act)
        self.fileToolBar.addAction(self.export_cache_act)
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

    def __create_statusbar__(self):
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

    def __create_dock_windows__(self):
        """ Creates and organizes all dockable windows"""
        
        # Cache file browser 
        dock = QtGui.QDockWidget("Browser", self)
        dock.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.treeWidget = QtGui.QTreeWidget(dock)
        self.treeWidget.setObjectName('ICECacheInspectorWidget')
        self.treeWidget.setColumnCount(2)
        self.treeWidget.headerItem().setText(0, 'Item')
        self.treeWidget.headerItem().setText(1, 'Value')
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.handle_browser_contextmenu)
        self.treeWidget.setStyleSheet(CONSTS.SS_BACKGROUND)
        # ... browser context menus
        self.browser_contextmenu = QtGui.QMenu(self)
        self.browser_contextmenu.setStyleSheet(CONSTS.SS_MENU)
        self.browser_contextmenu.addAction(self.load_cache_data_act)
        self.browser_contextmenu.addAction(self.export_selected_cache_act)
        self.attribute_contextmenu = QtGui.QMenu(self)
        self.attribute_contextmenu.setStyleSheet(CONSTS.SS_MENU)
        self.attribute_contextmenu.addAction(self.load_cache_data_act)
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

    def handle_browser_contextmenu(self, point):
        """ Context menus for exporting cache files and loading attributes data """
        item = self.treeWidget.currentItem() 
        
        # show browser context menu on the widget
        if item.parent() != None and item.text(0) != 'Attribute':
            return
        
        if item.text(0) == 'Attribute':
            self.attribute_contextmenu.exec_(self.treeWidget.mapToGlobal(point))
        else:
            action = self.browser_contextmenu.exec_(self.treeWidget.mapToGlobal(point))
            if action == self.export_selected_cache_act:
                var = item.data(0, QtCore.Qt.UserRole)
                filename = var.toString()
                self.exporter_thread.export_files([filename], r'c:\temp', ('Color___', 'Size___'))                

    # Progress bar helpers
    def __start_progressbar__(self,num,msg=''):        
        self.pbar.show()
        self.pbar.setRange(0, num)
        self.pbar.setValue(1)
        self.middle_msg.setText( msg )

    def __update_progressbar__(self):        
        self.pbar.setValue(self.pbar.value() + 1)        

    def __stop_progressbar__(self):        
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
