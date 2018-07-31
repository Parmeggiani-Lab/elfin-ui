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
    * Should a symmetric hub network be allowed to have asymmetric hubs in its arms? 
        * This is currently allowed
        * In strctures like `<asy_hub - sym_hub - asy_hub>` should the symetric property propogate and force  each arm of the asy_hub to also be identical?

 2. Mirrored modules
 	* Symmetric hub extrusions are automatically mirrored.
 	* Other modules can be mirror-linked by the Link by Mirror operator.
 	* When extruding from a module that has "mirrors" to other modules of the same protoype, the newly extruded modules will also be mirror-linked together.
 		* Only intra-network auto mirroring is supported.
 		* For inter-network simultaneous extrusion, first select one member of each mirror-link group, and then use the Select Mirror Links operator.

### TODO: Current Working On:
 * Link by Mirror and Select Mirror Links operator
 * Track symmetric mother hub? Is this necessary? 
 * Make C/N term extrusion share more code

### TODO: Must-Haves
 * Enforce hub symmetry through modifier-like behaviour
 * Define auto-design "work sites" by drawing path guides
 * Export to Elfin Core format

### TODO: Nice-to-Haves
 * Pull-Join: join two module networks by pulling first selected network to the second one.
	 1. Check compatibility
	 2. Then do a frame re-shift for all objs in first network based on the selected module
	 * Allow pull-join having one side being symmetric core?
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