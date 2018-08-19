# elfin-ui

A Blender addon that serves [elfin](https://github.com/joy13975/elfin)'s frontend user interface for building large proteins using protein modules.


<p align="center">
<img src="resources/images/simultaneous_extrusion.gif" width="70%">
</p>


## [Skip to: Getting Started](#getting-started)

## Goals

 * Enable full assembly design through manual manipulation of modules and networks.
 * Enable partially automated (with [elfin-solver](https://github.com/joy13975/elfin-solver)) design through path guides.

## Development Notes:

 1. Symmetric hubs
 	* There are only two symmetric hubs in the database right now. 
 	* All "arms" of a symmetric hub must be identical, and because of this, any network can only logically have zero or one symmetric hub "core".
    * Should a symmetric hub network be allowed to have asymmetric hubs in its arms? 
        * This is currently allowed.

 2. Mirror-linked modules
 	* Symmetric hub extrusions are automatically mirrored.
 	* Other modules can be mirror-linked by the Link by Mirror operator.
 	* When extruding from a module that has "mirrors" to other modules of the same protoype, the newly extruded modules will also be mirror-linked together.
 		* Only intra-network auto mirroring is supported.
 		* For inter-network simultaneous extrusion, first select one member of each mirror-link group, and then use the Select Mirror Links operator.

### TODO: Currently Working On:
 * Connect Joints operator

### TODO: Must-Haves
 * Export to Elfin Core format

### TODO: Nice-to-Haves
 * Pull-Join Operator: join two module networks by pulling first selected network to the second one.
	 1. Check compatibility
	 2. Then do a frame re-shift for all objs in first network based on the selected module
	 * Allow pull-join having one side being symmetric core?
 * Confirm deletion caused by collision
 	* Collision detection using single module 3D models are not very accurate (currently each module is shrunken to 85% before checking).
 * Incremental selection
 	 * We already have a Select Network oeprator though

### TODO: Feasibility N/A
 * Select previous module upon module delete
 * Auto-seek extrusion
 	 * List all extrudable termini of the network that the selected module belongs to.
	 * If there are hubs in the network there might be multiple heads. In this case ask the user to choose one.
		
### TO-CHANGE: Once Blender gets an API upgrade
 * Hooking callback upon object deletion or entrance to scene
 	 * In v2.79 there are no callback hooks for object deletion/entrance.
 	 * Currently implemented using a watcher that checks the scene objects at 100ms intervals, which can be flacky under rare circumstances e.g. if the user uses a script to edit the scene at non-human speeds. For the most part this works, but is obviously not the best approach.
 * Hub symmetry enforcement
 	 * In v2.79, we're not able to create custom modifiers in Python.
 	 * Currently implemented using mirror-linking.

## Getting Started

Get [Blender v2.79b](https://builder.blender.org/download/).

This addon was developed for and tested on Blender v2.79. 

Beware that Blender v2.8 (now beta) will probably introduce significant changes so it's best to stay away for now.

After you've downloaded Blender, run it and go to `File` > `User Preferences` and click `Save User Settings`. This has to be done at least once to create your Blender use profile.

Next, refer to:

### [Tutorial With GIFs](resources/images/tutorial/README.md)