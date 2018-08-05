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
 	* All "arms" of a symmetric hub must be identical and because of this, any network can only logically have zero or one symmetric hub "core".
    * Should a symmetric hub network be allowed to have asymmetric hubs in its arms? 
        * This is currently allowed
        * In strctures like `<asy_hub - sym_hub - asy_hub>` should the symetric property propogate and force  each arm of the asy_hub to also be identical?

 2. Mirror-linked modules
 	* Symmetric hub extrusions are automatically mirrored.
 	* Other modules can be mirror-linked by the Link by Mirror operator.
 	* When extruding from a module that has "mirrors" to other modules of the same protoype, the newly extruded modules will also be mirror-linked together.
 		* Only intra-network auto mirroring is supported.
 		* For inter-network simultaneous extrusion, first select one member of each mirror-link group, and then use the Select Mirror Links operator.

### TODO: Currently Working On:
 * Select Network operator

### TODO: Must-Haves
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

[Tutorial With Screenshots](resources/images/tutorial/README.md)

## Installing (Linux/MacOS/WSL)

`./install`

For "pure" Windows (non-WSL), either copy the `elfin` folder to your Blender's addon directory or create a symlink via `mklink` or [Shell Link Extension](http://schinagl.priv.at/nt/hardlinkshellext/linkshellextension.html)

After installing, open Blender and go to `File > User Preferences > Add-ons` and search for `Elfin`. If the installation was successful there should be a `Elfin: Elfin UI`. Tick the box and make sure to `Save User Settings` (bottom-left).

## Updating the Module Library
The module library files are automatically fetched by `./install` but if in any case the module library was lost, modified, or became outdated, do:

`./fetch_library`

## Warnings Before Use
Any design created as of now will most likely not be exportable to elfin's internal data format when the export function is available. This is because Blender objects created using an old version of the addon will not get new properties even if the addon is updated. The protein design will need to be re-created.

We could possibly make future changes backword compatible by implementing a remove-all, re-add all function but right now this does not exist yet so be warned nonetheless.

## Using the Addon
All functionalities of the Elfin UI addon are accessed via what Blender calls "operators".

Effectively, when your mouse is within the viewport, you can hit <kbd>space</kbd> to bring up a search menu that lets you type in the name of the operator.

<p align="center">
<img src="resources/images/ui_tutorial_place.png" width="70%">
</p>

### Operators

Currently implemented operators:
 * <b>Place Module</b>
  	* Adds a new module to the scene at origin.
    * Only available <b>when nothing is selected</b> in the scene
 * <b>Extrude N</b> 
 	* Add a module to the N-Terminus of the selected module.
 	* Only available when one or more modules are selected
 * <b>Extrude C</b>
 	* Add a module to the C-Terminus of the selected module.
 	* Only available when one or more modules are selected
 * <b>Link by Mirror</b>
 	* Link multiple modules of the same prototype by mirror.
 	* Only available when one or more <b>homogenous modules</b> are selected (same prototype)
 * <b>Unlink Mirrors</b>
 	* Unlink mirrors from all selected modules.
 	* Only available when one or more modules are selected.
 * <b>List Mirrors</b>
 	* List mirror links of one selected module.
 	* Only available when <b>exactly one</b> module is selected.

You don't have to type the full name of the module. For example, "ex n" will bring up the <b>Extrude N</b> operator.

### Prototype Lists and Naming Convention

<p align="center">
<img src="resources/images/ui_tutorial_names.png" width="70%">
</p>

Place and Extrude operators will prompt you with a filtered list of actionable modules - let's call them <em>filtered prototypes</em>. There could be many modules in a scene, but modules with the same module name (not Blender name) are of the same prototype (like what classes are to objects). For extrusion, prototypes are filtered by compatibility and also terminus occupancy (i.e. is the N and/or C terminus already occupied?).

In the filtered prototype list, you will see that the name of a module is bounded by two period marks. These marks are sentinels which makes it easy to search the exact module one is looking for. Try typing just `D4` in the <b>Place</b> operator, and see what happens when you type `.D4` or `D4.` or `.D4.`.

The first letter, if there is one, denotes the <b>C Terminus</b> chain ID of the extrusion. This is needed because hub modules have more than one chain to extrude to and from.

The last letter is therefore the <b>N Terminus</b> chain ID in the to-be-extruded module.

### Coloring
The colour of each newly added module is set randomly. If you wish to set them manually, you can open the left-hand-side panel (via <kbd>t</kbd>) to adjust the color when the operator is <em>active</em> (when you've selected it after typing it). It's highly recommended that you change the color while the prototype selection is set to the `-Change Color-` placeholder. This is because with each color change Blender removes the object it added and re-adds it with a different color. That can cause considerable lag if you drag the colour sampler around the palette. You can also go into the material of the module object on the right-most side panel when the operator options are gone.

### Mirror-Linking
Mirror-linking was originally implemented to enforce symmetric execution of extrusion or deletion on the arms of a symmetric hub. I thought this could be potentially useful for manual design so I've made this available to the user via operators.

Mirror-linked modules essentially share extrusion and deletion operations. That means if you select just one of a mirror-linked group of modules and do extrusion on it, all other mirror-linked modules will also receive the same operation

### Useful Blender shortcuts:
 * <kbd>a</kbd> toggle select all/deselect all
 * <kbd>c</kbd> brush-select
 * <kbd>x</kbd> delete selection (with confirmation)
 * <kbd>r</kbd> rotate selection
 * <kbd>g</kbd> translate selection
 * <kbd>s</kbd> scale selection. <b>WARNING: Never scale modules. We need to keep the scale factor!</b>
 * <kbd>t</kbd> toggle left-hand-side panel (which has the Operator Properties panel)
 * <kbd>n</kbd> toggle right-hand-side panel (which has properties such as location, rotation and many more)
 * <kbd>cmd</kbd>+<kbd>z</kbd> undo
 * <kbd>cmd</kbd>+<kbd>shift</kbd>+<kbd>z</kbd> redo

Where <kbd>cmd</kbd> is involved, it's <kbd>ctrl</kbd> for Windows and Linux

### Collision Detection
By default collision detection is done on extrusion and placement of modules. The calculation is not perfect because we're using single module 3D models instead of their true atomic representation. If for any reason you need to disable this, you can find the tickbox in the left-hand-side panel (toggle by <kbd>t</kbd>).