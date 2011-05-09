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

# This is only needed for Python v2 but is harmless for Python v3.
import sip
sip.setapi('QString', 2)

import logging
logging.basicConfig()

from PyQt4 import QtCore, QtGui
from iceexplorer import ICECacheExplorerWindow

if __name__ == '__main__':

    import sys
    notice = 'ICE Cache Explorer Copyright (C) 2010  M.A.Belzile'
    print notice
    app = QtGui.QApplication(sys.argv)
    mainWin = ICECacheExplorerWindow()
    mainWin.show()
    sys.exit(app.exec_())
