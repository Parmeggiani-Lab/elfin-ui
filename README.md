# Elfin UI

A Blender addon that serves [elfin](https://github.com/joy13975/elfin)'s frontend user interface for building large proteins using protein modules.


<p align="center">
<img src="resources/images/simultaneous_extrusion.gif" width="70%">
</p>


## [Skip to: Getting Started](#getting-started)

## Goals

 * Enable full assembly design through manual manipulation.
 * Enable partially automated (with [elfin-solver](https://github.com/joy13975/elfin-solver)) design through path guides.

### TODO: Current Working On:
 * Mirrored single-hub extrude (no symmetric hubs here)
 * Mirrored delete & clean up
 * Mirror link operator
 * Track symmetric mother hub? Is this necessary? 

### TODO: Must-Haves
 * Enforce hub symmetry through modifier-like behaviour
 * Define Elfin Core work area by drawing path guide
 * Export to Elfin Core format

### TODO: Nice-to-Haves
 * Pull-Join: join two module networks by pulling first selected network to the second one.
	 * First check compatibility
	 * Then simply do a frame re-shift for all objs in first network based on the selected module
 * Allow user to confirm deletion when collision is detected
 * Incremental selection
 	 * Don't think Blender has API for this yet but we could add an operator.
 * Select previous module upon module delete (?)
 * Auto-seek extrusion (?)
	 * If there are multiple heads, then tell the user.
	 * If there is too much time left then we could add a selection prompt.
		
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