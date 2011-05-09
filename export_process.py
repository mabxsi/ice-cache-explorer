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
import shutil
from icereader import *
from h5reader import *
from consts import CONSTS

def main(argv):
    
    files = eval(argv[1])
    exportdir = argv[2]
    exportfmt = int(argv[3])

    if not os.path.exists( exportdir ):
        os.mkdir( exportdir, 777 )
    
    # export input files
    for f in files:
        ext = os.path.splitext(f)[1]
        r = None
        try:
            if ext == '.sih5' or ext == '.hdf5':
                r = H5Reader( f )            
            elif ext == '.icecache':
                r = ICEReader( f )                        
        except:
            sys.stderr.write( 'Export process failed to load data: %s' % f )
            sys.stderr.flush()
            continue
        
        try:
            r.export(exportdir,exportfmt)
        except:
            sys.stderr.write( 'Export process failed to export: %s' % f )    
            sys.stderr.flush()     
            continue
    
        # send the exported file to process output
        sys.stdout.write( f )
        sys.stdout.flush()   
   
if __name__ == '__main__':
    main(sys.argv)
