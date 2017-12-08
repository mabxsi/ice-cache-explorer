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

# Loading ICECache Data #
You can either load a folder containing a sequence of .icecache or .siH5   files (HDF5 format):
  * File | Load Cache Folder ...

Or one or multiple .icecache/.siH5 files.
  * File | Load Cache File ...

# Drag and Drop #
.icecache/.siH5 file(s) or folder can also be drag and dropped on the 3D view as an alternative for loading files.

# Export To Text #
Cache files can be exported to ascii files:
  * File | Export Folder to Text ...
  * File | Export Caches to Text ...

# Export To .siH5 #
Cache files can be exported to HDF5 file format (.siH5):
  * File | Export Folder to SIH5 ...
  * File | Export Caches to SIH5 ...

note: The target folder defaults to 'c:\temp' or \var\tmp on linux. The default can be changed from the Preferences dialog (Edit|Preferences)

You can also export caches from the Browser window: right-click on a Cache or Attribute item.

# Cancel operation #
File load and export operations can be stopped by clicking on the Cancel button located in the File toolbar or by selecting the File|Cancel menu item.

# Viewing #
You can navigate in the 3D view with one of these tools: pan, orbit and zoom. They are all located in the 'Tools' toolbar. You can use presets to set the 3D view: perspective, top, front, right. These presets can be selected from the 'View' toolbar.

# Browser #
The Browser window contains a tree widget for listing loaded files information. The widget is updated when the cache files are being loaded. Note: Expanding the Attribute Data item can be long depending of the size of the data.

# Playback #
The play back window allows you to animate a sequence of cache files.

## Controls ##
  * > Play a sequence. Releasing the button stops the sequence.
  * >. Play one frame forward.
  * .< Play one frame backward.
  * >| Move the playback cursor to end.
  * |< Move the playback cursor to start.
  * @ When the repeat button is pressed, the sequence can be played continously.
  * edit fields: start and end cache number can be specified.
  * Cursor: Move the cursor to scroll through cache files.

# Preferences #
This dialog is used for setting default values. The default export folder and number of processes is currently supported. More preferences are planned in a future release.

# Limitations #
  1. The 3D viewer supports these attributes only: PointPosition, Color
  