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

# This is only needed for Python v2 but is harmless for Python v3.
#import sip
#sip.setapi('QString', 2)

from PyQt4 import QtCore, QtGui

class PlaybackWidget( QtGui.QWidget ):
    #slots
    startcacheChanged = QtCore.pyqtSignal(int) 
    endcacheChanged = QtCore.pyqtSignal(int) 
    cacheChanged = QtCore.pyqtSignal(int) 
    playChanged = QtCore.pyqtSignal() 
    stopChanged = QtCore.pyqtSignal() 
    loopChanged = QtCore.pyqtSignal( bool ) 
    
    def __init__( self, viewer, parent=None ):
        super( PlaybackWidget, self).__init__(parent)

        #self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        self.current_cache = 1
        self.start_cache = 1
        self.end_cache = 100

        self.playtoggle = QtGui.QPushButton( 'Play', self)
        self.playtoggle.setFixedWidth(50)
        self.playtoggle.setCheckable( True )
        self.stepforward = QtGui.QPushButton('>',self)
        self.stepforward.setFixedWidth(50)
        self.stepbackward = QtGui.QPushButton('<',self)
        self.stepbackward.setFixedWidth(50)
        self.gotoend = QtGui.QPushButton('>>',self)
        self.gotoend.setFixedWidth(50)
        self.gotostart = QtGui.QPushButton('<<',self)
        self.gotostart.setFixedWidth(50)
        self.loop = QtGui.QPushButton('Loop',self)
        self.loop.setFixedWidth(50)
        self.loop.setCheckable( True )
        
        self.cache_label = QtGui.QLabel(str(self.start_cache), self)

        self.startcache = QtGui.QLineEdit(self)
        self.startcache.setValidator( QtGui.QIntValidator() )
        self.startcache.setFixedWidth(30)
        self.startcache.setText(str(self.start_cache))
        self.endcache = QtGui.QLineEdit(self)
        self.endcache.setValidator( QtGui.QIntValidator() )
        self.endcache.setFixedWidth(30)
        self.endcache.setText(str(self.end_cache))
        
        self.timeline = QtGui.QSlider( QtCore.Qt.Horizontal, parent )
        self.timeline.setRange(self.start_cache, self.end_cache)
        self.timeline.setSingleStep(1)
        self.timeline.setPageStep(10)
        self.timeline.setTickInterval(1)
        self.timeline.setTickPosition(QtGui.QSlider.TicksRight)

        hbox = QtGui.QHBoxLayout()      
        hbox.addWidget(self.startcache)
        hbox.addWidget(self.timeline)
        hbox.addWidget(self.endcache)
        hbox.setStretchFactor(self.startcache,1)
        hbox.setStretchFactor(self.timeline,20)
        hbox.setStretchFactor(self.endcache,1)
        
        hbox2 = QtGui.QHBoxLayout()    
        hbox2.setSpacing(10)
        hbox2.addStretch(10)
        hbox2.addWidget(self.gotostart)         
        hbox2.addWidget(self.stepbackward)         
        hbox2.addWidget(self.playtoggle)         
        hbox2.addWidget(self.stepforward)         
        hbox2.addWidget(self.gotoend)
        hbox2.addWidget(self.loop)    
        hbox2.addStretch(10)

        hbox3 = QtGui.QHBoxLayout()    
        hbox3.addStretch(10)
        hbox3.addWidget(self.cache_label)    
        hbox3.addStretch(10)
        
        vbox = QtGui.QVBoxLayout()      
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox)
        vbox.addLayout(hbox2)
        vbox.addStretch(10)
        
        self.setLayout(vbox)

        self.__setup_signals__(viewer)

    def __block_signals__( self, bFlag ):
        self.timeline.blockSignals( bFlag )
        self.startcache.blockSignals( bFlag )
        self.endcache.blockSignals( bFlag )
        self.stepforward.blockSignals( bFlag )
        self.stepbackward.blockSignals( bFlag )
        self.gotostart.blockSignals( bFlag )
        self.gotoend.blockSignals( bFlag )
        self.playtoggle.blockSignals( bFlag )
        self.loop.blockSignals( bFlag )

    def __setup_signals__(self,viewer):
        self.timeline.valueChanged.connect(self.on_cache_change )
        self.startcache.textChanged.connect(self.on_start_cache_change )
        self.endcache.textChanged.connect(self.on_end_cache_change )
        self.startcache.editingFinished.connect(self.on_start_cache_final_change )
        self.endcache.editingFinished.connect(self.on_end_cache_final_change )
        self.stepforward.pressed.connect( self.on_stepforward_pressed )
        self.stepbackward.pressed.connect( self.on_stepbackward_pressed )
        self.gotostart.pressed.connect( self.on_gotostart_pressed )
        self.gotoend.pressed.connect( self.on_gotoend_pressed )
        self.playtoggle.toggled.connect( self.on_playtoggled )
        self.loop.toggled.connect( self.on_looptoggled )
        viewer.beginCacheLoading.connect(self.on_begin_cache_loading)
        viewer.cacheLoaded.connect(self.on_cache_loaded)
        viewer.endCacheLoading.connect(self.on_end_cache_loading)
        viewer.beginDrawCache.connect(self.on_begin_drawcache)
        viewer.endDrawCache.connect(self.on_end_drawcache)
        viewer.beginPlayback.connect(self.on_begin_playback)
        viewer.endPlayback.connect(self.on_end_playback)        
        
    def on_playtoggled( self ):
        if self.playtoggle.isChecked() == True:
            # prevent unecessary notifications from the timeline widget
            self.timeline.blockSignals(True)            
            self.playChanged.emit( )
        else:
            # reactivate notifications from the timeline widget
            self.timeline.blockSignals(False)            
            self.stopChanged.emit( )

    def on_looptoggled( self ):
        self.loopChanged.emit( self.loop.isChecked() )

    def on_cache_change( self, cache ):
        #print 'PlaybackWidget.on_cache_change %d' % (cache)
        self.current_cache = cache
        #self.cache_label.setText('Cache: %d' % cache )
        self.cache_label.setText( str(self.current_cache) )
        self.cacheChanged.emit( cache )        

    def on_start_cache_change( self, cache ):
        if cache:
            self.start_cache = int(cache)

    def on_end_cache_change( self, cache ):
        if cache:
            self.end_cache = int(cache)

    def on_start_cache_final_change( self ):
        self.startcacheChanged.emit( self.start_cache )
        self.timeline.setValue( self.start_cache )
        self.timeline.setRange(self.start_cache, self.end_cache)        

    def on_end_cache_final_change( self ):
        self.endcacheChanged.emit( self.end_cache )
        self.timeline.setValue( self.end_cache )
        self.timeline.setRange(self.start_cache, self.end_cache)        

    def on_stepforward_pressed( self ):
        self.current_cache += 1
        if self.current_cache > self.end_cache:
            self.current_cache = self.end_cache
        
        self.timeline.setValue( self.current_cache )

    def on_stepbackward_pressed( self ):
        self.current_cache -= 1
        if self.current_cache < self.start_cache:
            self.current_cache = self.start_cache
            
        self.timeline.setValue( self.current_cache )

    def on_gotostart_pressed( self ):
        self.current_cache = self.start_cache            
        self.timeline.setValue( self.current_cache )

    def on_gotoend_pressed( self ):
        self.current_cache = self.end_cache
        self.timeline.setValue( self.current_cache )

    def on_begin_cache_loading( self, cache_count, start_cache, end_cache ):
        #print 'PlaybackWidget.on_begin_cache_loading %d %d %d' % (cache_count, start_cache, end_cache)

        self.current_cache = start_cache
        self.start_cache = start_cache
        self.end_cache = end_cache
        self.timeline.setRange(self.start_cache, self.end_cache)        
        self.timeline.setValue( self.current_cache )
        self.startcache.setText( str(self.start_cache) )
        self.endcache.setText( str(self.end_cache) )

        self.__block_signals__(True)

    def on_cache_loaded( self, cache, reader ):
        #print 'PlaybackWidget.on_cache_loaded %d ' % (cache)
        self.current_cache = cache
        self.timeline.setValue( self.current_cache )
        #self.cache_label.setText('Cache: %d' % self.current_cache )
        self.cache_label.setText( str(self.current_cache) )

    def on_end_cache_loading( self, cache_count, start_cache, end_cache ):
        self.__block_signals__(False)

    def on_begin_drawcache( self, cache, bFileLoading ):
        #print '\nPlaybackWidget.on_begin_drawcache %d loading=%d' % (cache,bFileLoading)
        pass
        
    def on_end_drawcache( self, cache, bFileLoading ):
        #print 'PlaybackWidget.on_end_drawcache %d loading=%d\n' % (cache,bFileLoading)
        self.current_cache = cache
        #self.cache_label.setText('Cache: %d' % cache )        
        self.cache_label.setText( str(self.current_cache) )
        self.timeline.setValue( self.current_cache )
        
    def on_begin_playback( self ):
        pass

    def on_end_playback( self ):        
        if self.loop.isChecked() == False:
            self.playtoggle.setChecked(False)
            
