# Sublime Text 2 Actionscript 3 Package #

This package provides multiple features for working with Actionscript 3 projects in [http://www.sublimetext.com/](Sublime Text 2).  I wasn't satisfied with any of the existing AS3 packages so I decided to write my own from scratch. Still in an experimental state.

Note: This package assumes that your source files in your project all live under a common directory name (default "src/", configurable in as3.py).

Features include:

### Syntax Highlighting ###

Syntax highlighting support for .as files and AS3 embedded in .mxml files.  A few regular expressions were borrowed from [https://github.com/simongregory/actionscript3-tmbundle](https://github.com/simongregory/actionscript3-tmbundle).

### Snippets ###

Basic snippets for common language elements (see /Snippets)

### Build systems ###

Basic build systems for compiling to .swf and .swc files, and generating AsDoc documentation.  More complex projects will likely require custom build systems but you can use these as a starting point.

### Plugins ###

Several commands for automating common tasks in AS3 development, accessible via the Command Palette.

Commands at this time include:

*	New class/interface/event.  Create new source files quickly.
*	Import class.  Quickly search for and import a class.
*	Extract interface.  Create a new interface using the public functions of a class.  Can also be useful to quickly view the API of a large class, even if you don't want to create an interface.
*	More planned...


## Install ##

Clone this repository (or download and unzip) in your packages folder.


## License ##

See LICENSE.txt