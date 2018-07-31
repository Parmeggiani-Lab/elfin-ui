# Elfin UI

A Blender addon that serves [elfin](https://github.com/joy13975/elfin)'s frontend user interface for building large proteins using protein modules.


<p align="center">
<img src="resources/images/simultaneous_extrusion.gif" width="70%">
</p>


## [Skip to: Getting Started](#getting-started)

## Goals

 * Enable full assembly design through manual manipulation.
 * Enable partially automated (with [elfin-solver](https://github.com/joy13975/elfin-solver)) design through path guides.

## Development Notes:

 1. Symmetric hubs
 	* There are only two symmetric hubs in the database right now. 
 	* All "arms" of a symmetric hub must be identical and because of this, logically any network can only have zero or one symmetric hub "core".
    * Should a symmetric hub network be allowed to have asymmetric hubs in its arms? In strctures like `<asy_hub - sym_hub - asy_hub>` would the asy_hubs also have "arms" that need to be symmetric because of the mother sym_hub?

### TODO: Current Working On:
 * Mirrored single-hub extrude for networks with a symmetric hub core
 * Mirrored delete & clean up
 * Mirror link operator
 * Track symmetric mother hub? Is this necessary? 
 * Make C/N term extrusion share more code

### TODO: Must-Haves
 * Enforce hub symmetry through modifier-like behaviour
 * Define auto-design "work sites" by drawing path guides
 * Export to Elfin Core format

### TODO: Nice-to-Haves
 * Pull-Join: join two module networks by pulling first selected network to the second one.
	 * First check compatibility
	 * Then simply do a frame re-shift for all objs in first network based on the selected module
 * Allow user to confirm deletion when collision is detected. Collision detection using single module 3D models are not very accurate (currently each module is shruken to 85% before checking).

### TODO: Maybe?
 * Incremental selection
 	 * Don't think Blender has API for this yet but we could add an operator.
 * Select previous module upon module delete (possible ?)
 * Auto-seek extrusion
	 * If there are hubs in the network there might be multiple heads. In this case ask the user to choose one.
		
### TO-CHANGE: Once Blender gets an API upgrade
 * Hooking callback upon object deletion or entrance to scene
 	 * In v2.79 there are no callback hooks for object deletion/entrance.
 	 * Currently implemented using a watcher at 100ms, which can be flacky under rare circumstances e.g. if the user uses a script to edit the scene at non-human speeds.
 * Hub symmetry enfrocement
 	 * In v2.79, we're not able to create custom modifiers in Python.
 	 * Currently implemented using \<TBD\>

## Getting Started

Get [Blender v2.79b](https://builder.blender.org/download/).

This addon was developed for and tested on Blender v2.79. 

Beware that Blender v2.8 (now beta) will probably introduce significant changes so it's best to stay away for now.

## Installing (Linux/MacOS/WSL)

`./install`

For pure Windows (non-WSL), either copy the `elfin` folder to your Blender's addon directory or create a symlink via `mklink` or [Shell Link Extension](http://schinagl.priv.at/nt/hardlinkshellext/linkshellextension.html)

## Updating the Module Library

If in any case the module library was lost, modified, or became outdated, do:

`./fetch_library`