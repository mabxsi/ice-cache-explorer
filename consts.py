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

class CONSTS:    
    siICENodeContextAny           =0x3f                 # from enum siICENodeContextType
    siICENodeContextComponent0D   =0x2                  # from enum siICENodeContextType
    siICENodeContextComponent0D2D =0x10                 # from enum siICENodeContextType
    siICENodeContextComponent0DOr1DOr2D=0xe             # from enum siICENodeContextType
    siICENodeContextComponent1D   =0x4                  # from enum siICENodeContextType
    siICENodeContextComponent2D   =0x8                  # from enum siICENodeContextType
    siICENodeContextElementGenerator=0x20               # from enum siICENodeContextType
    siICENodeContextNotSingleton  =0x3e                 # from enum siICENodeContextType
    siICENodeContextSingleton     =0x1                  # from enum siICENodeContextType
    siICENodeContextSingletonOrComponent0D=0x3          # from enum siICENodeContextType
    siICENodeContextSingletonOrComponent0D2D=0x11       # from enum siICENodeContextType
    siICENodeContextSingletonOrComponent1D=0x5          # from enum siICENodeContextType
    siICENodeContextSingletonOrComponent2D=0x9          # from enum siICENodeContextType
    siICENodeContextSingletonOrElementGenerator=0x21    # from enum siICENodeContextType
    
    siICENodeDataAny              =0x7ffff    # from enum siICENodeDataType
    siICENodeDataArithmeticSupport=0x41fe     # from enum siICENodeDataType
    siICENodeDataBool             =0x1        # from enum siICENodeDataType
    siICENodeDataColor4           =0x200      # from enum siICENodeDataType
    siICENodeDataCustomType       =0x10000    # from enum siICENodeDataType
    siICENodeDataExecute          =0x1000     # from enum siICENodeDataType
    siICENodeDataFloat            =0x4        # from enum siICENodeDataType
    siICENodeDataGeometry         =0x400      # from enum siICENodeDataType
    siICENodeDataIcon             =0x40000    # from enum siICENodeDataType
    siICENodeDataInterface        =0x400      # from enum siICENodeDataType
    siICENodeDataLocation         =0x800      # from enum siICENodeDataType
    siICENodeDataLong             =0x2        # from enum siICENodeDataType
    siICENodeDataMatrix33         =0x80       # from enum siICENodeDataType
    siICENodeDataMatrix44         =0x100      # from enum siICENodeDataType
    siICENodeDataMultiComp        =0x43f8     # from enum siICENodeDataType
    siICENodeDataQuaternion       =0x40       # from enum siICENodeDataType
    siICENodeDataReference        =0x2000     # from enum siICENodeDataType
    siICENodeDataRotation         =0x4000     # from enum siICENodeDataType
    siICENodeDataShape            =0x8000     # from enum siICENodeDataType
    siICENodeDataString           =0x20000    # from enum siICENodeDataType
    siICENodeDataValue            =0x7c3ff    # from enum siICENodeDataType
    siICENodeDataVector2          =0x8        # from enum siICENodeDataType
    siICENodeDataVector3          =0x10       # from enum siICENodeDataType
    siICENodeDataVector4          =0x20       # from enum siICENodeDataType
    
    siICENodeStructureAny=0x3
    siICENodeStructureArray =0x2      # from enum siICENodeStructureType
    siICENodeStructureSingle =0x1      # from enum siICENodeStructureType
    
    siICEAttributeCategoryUnknown = 0
    siICEAttributeCategoryBuiltin = 1
    siICEAttributeCategoryCustom = 2    
    
    siICENodeObjectPointCloud = 0
    siICENodeObjectPolygonMesh = 1
    siICENodeObjectNurbsMesh = 2
    siICENodeObjectNurbsCurve = 3
    
    siICEShapePoint		=0
    siICEShapeSegment	=1
    siICEShapeDisc		=2
    siICEShapeRectangle	=3
    siICEShapeSphere	=4
    siICEShapeBox		=5
    siICEShapeCylinder	=6
    siICEShapeCapsule	=7
    siICEShapeCone		=8
    siICEShapeBlob		=9
    siICEShapeInstance  =128
    siICEShapeReference	=129
    
    siICECacheV100    = 100
    siICECacheV101    = 101
    siICECacheV102    = 102
    siICECacheV103    = 103

    SS_MENUBAR = "\
        QMenuBar {\
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgb(235,235,235), stop:1 rgb(205,205,205));\
        }\
        QMenuBar::item {\
            margin: 1px; \
            spacing: 1px; \
            padding: 1px 5px;\
            background: transparent;\
            border-radius: 2px;\
         }\
         QMenuBar::item:selected { \
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,stop:0 rgb(100,100,100), stop:.1 rgb(210,210,210), stop:1 rgb(230,230,230));\
            border: 1px solid darkgrey;\
         }\
        QMenuBar::item:pressed { \
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,stop:0 rgb(80,80,80), stop:.1 rgb(190,190,190), stop:1 rgb(210,210,210));\
            border: 1px solid darkgrey;\
        }"
    
    SS_MENU = "\
        QMenu {\
             background-color: rgb(205,205,205);\
             border: 1px solid black;\
         }\
         QMenu::item {\
             background-color: transparent;\
         }\
         QMenu::item:selected {\
             background-color: cornflowerblue;\
         }"        

    SS_BACKGROUND = "QWidget { background-color: rgb(204,204,204) }"

    # export format 
    TEXT_FMT = 0
    SIH5_FMT = 1
    ICECACHE_FMT = 2
    