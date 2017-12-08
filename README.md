# ICE Explorer

A 3D application written in python for viewing and reading Softimage ICE Cache 
files such as particle data. The application provides interactive tools for 
viewing the particles (playback, orbit, zoom, etc...), browsing cache data in a 
tree window and converting to ascii and HDF5 files.

# License
GNY General Public License v3 (see the LICENSE.txt file for details)
All files in the ice-cache-explorer repository are also covered.

# Documentation and usage
Instructions how to get going with ICE Explorer (beta 1)

# Requirements

These items are required by ICE Explorer and need to be installed first:

- [PyOpenGL](http://sourceforge.net/projects/pyopengl/)
- [PyQt](http://www.riverbankcomputing.co.uk/software/pyqt/download)
- [NumPy](http://sourceforge.net/projects/numpy/files/)
- [H5py](https://code.google.com/p/h5py/downloads/list)

Note: to avoid compiling these modules you can download precompiled versions from this site:

http://www.lfd.uci.edu/~gohlke/pythonlibs/

# How to download the code
```
git clone https://github.com/mabxsi/ice-cache-explorer 
```

# How To Run
From the installation folder: python main.py

# Loading ICECache Data
You can either load a folder containing a sequence of .icecache or .siH5 files (HDF5 format): * File | Load Cache Folder ...
Or one or multiple .icecache/.siH5 files. * File | Load Cache File ...