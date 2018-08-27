# Tutotial Content
1. [Installing](#installing)
2. [Updating](#updating)
3. [Warnings Before Use](#warnings-before-use)
4. [Usage](#usage)
5. [Operator List](#operator-list)
6. [Prototype Naming Convention](#prototype-naming-convention)
7. [Coloring](#coloring)
8. [Mirror-Linking](#mirror-linking)
9. [Useful Blender Shortcuts](#useful-blender-shortcuts)
10. [Collision Detection](#collision-detection)

# Installing


```
git clone --depth 1 git@github.com:joy13975/elfin-ui
cd elfin-ui
./install
```

This should work for Linux/MacOS/WSL.

For "pure" Windows (non-WSL), either copy the `elfin` folder to your Blender's addon directory or create a symlink via `mklink` or [Shell Link Extension](http://schinagl.priv.at/nt/hardlinkshellext/linkshellextension.html)

After installing, open Blender and go to `File > User Preferences > Add-ons` and search for `Elfin`. If the installation was successful there should be a `Elfin: Elfin UI`. Tick the box and make sure to `Save User Settings` (bottom-left).

<p align="center">
<img src="download_and_install.png" width="85%">
</p>

Before enabling, your Blender probably looks like:
<p align="center">
<img src="before_blender_prefs.png" width="85%">
</p>

After enabling, your Blender should look like:
<p align="center">
<img src="after_blender_prefs.png" width="85%">
</p>

Notice that the left-hand-side panel now has an `elfin` section with some debug buttons. You don't need to touch these buttons as they are for debugging. You might sometimes find a need for disabling collision detection or resetting the properties. There are facilities for processing PyMol-generated .obj module models but for now we don't need to get into that.


# Updating

To update to the latest elfin-ui, simply pull (inside elfin-ui root folder):

`git pull`

The module library files are automatically fetched by `./install` but if in any case the module library was lost, modified, or became outdated, do:

`./fetch_library`

# Warnings Before Use
Any design created as of now may or may not be exportable to elfin's internal data format when the export function gets implemented. This is because Blender objects created using an old version of the addon will not get new properties even if the addon is updated. The protein design will need to be re-created.

We could possibly make future changes backword compatible by implementing a remove-all, re-add all function but right now this does not exist yet so be warned nonetheless.

There does not seem to be a clean way to detect whether a file was created by an older version of elfin-ui, and whether or not the older version is incompatible.

# Usage
The design paradigm of elfin-ui revolves around module assembly. This means the user is expected to creat modules, extrude from modules, move/rotate networks around, and draw path guides (upcoming feature which calls into elfin-solver for automatic segment creation).

All functionalities of the Elfin UI addon are accessed via what Blender calls "operators". Basically, when your mouse is within the viewport you can hit <kbd>space</kbd> to bring up a search menu that lets you type in the name of the operator.

The following are some basic examples of creating and manipulating modules.

## Adding a Module

There are two ways to spawn a single/hub module into the scene: through the `Add Module` operator or through Blender's primitives menu (<kbd>shift</kbd>+<kbd>a</kbd>). The former is more flexible because you can search the prototype list by typing the name instead of scrolling around. Below is a demonstration.

Move the cursor into Blender's viewport and hit <kbd>space</kbd>. Type in `place` and one item should read `Elfin: Add (place) a module` (the GIF is a bit outdated but the process is the same):

<p align="center">
<img src="place.gif" width="85%">
</p>

Hit <kbd>enter</kbd> and a prototype list should be displayed. You can select the module you want to place, or select `-Change Color-` in order to set the color before loading in the module's model. The selected module should get placed at origin in its default orientation.

<b>Note: </b> double modules are deliberately disabled, because they do not serve a purpose in elfin-ui's design paradigm.

<b>Optional: color setting.</b> Now that `Add Module` is activated, you can move your cursor away and set the color for the new module before loading the actual model by using the Operator Properties panel at the bottom-left corner. You don't have to do this because elfin-ui sets a new color randomly for each new module. You <em>can</em> still change the color after loading the model, but if you do that through the Operator Properties panel it will cause lag as Blender removes the model it had loaded and re-loads a new one with a different color. If you've already loaded the model and want to change the color, go into the lower half of the right-hand-side panel, find the `Material` tab (with a copper-colored ball icon) and you can change it there without causing lag.

<b>Optional: re-select prototype.</b> The Operator Properties panel also lets you "redo" - that is to choose again the module prototype to add (this is the same as viewport's prototype list).

## Extrusion

Again, hit <kbd>space</kbd> with the cursor in Blender's viewport. Type in `ext` and one item should read `Elfin: Extrude Module`. After selecting this item, a a list of extrudable termini will be displayed. If a terminus is occupied by an existing module, this list will filter accordingly. When prompted, select which terminus: `N` or `C`, to extrude. Then, choose your desired module.

In the following GIF I chose to extrude at the C-Terminus, then chose `-Change Color-`.

<p align="center">
<img src="extrude_c.gif" width="85%">
</p>

Select the module prototype the same way as with `Add Module`.

## Mirror Linking

Originally designed for enforcing symmetric hubs' arm identiticality, mirror linking cause simultaneous manipulation for two or more separate modules that are not necessarily spatially related.

When modules are <em>mirror-linked</em> (or <em>linked-by-mirror</em>), they are called a group of "mirrors". Any extrusion or deletion applied on any one of the mirrors will also be applied on the rest of the linked mirrors. Further, modules that are a result of extrusion from any mirror will also be automatically mirror-linked (between the new set of modules).

To link modules by mirror, search for `link by`. One item should read `Elfin: Link multiple modules of the same prototype by mirror`:

<p align="center">
<img src="mirror_linking.gif" width="85%">
</p>

Selected modules must be of the same prototype. 

If the linking was successful a message should be shown. If the selected modules already have mirrors linked, you will get a warning and a choice as to whether or not to replace existing links with new ones.

You can also list the mirrors of a module with the List Mirror opereator. You can select all mirrors of the currently selected module with `Select Mirrors`.

Try deleting one of the extruded modules and see what happens. Revert using <kbd>cmd</kbd>+<kbd>z</kbd> (<kbd>ctrl</kbd> for Windows and Linux).

Mirrors can have any location and rotation - they do not need to be identical. You can even move them (as long as you move the connected modules together) and they will stay linked.

<b>Helpful to know</b>: extruding from symmetric hubs are automatically mirror-linked. 

# Operator List

Currently implemented operators:
 * `Add Module` (formerly called "Place Module")
  	* Adds a new module to the scene at origin.
  	* Automatically creates a new network and places the newly added module under that network.
    * Only available <b>when nothing is selected</b>.
 * `Extrude Module` 
 	* Add a module to the N- or C-Terminus of the selected module.
 	* Only available <b>when one or more modules are selected</b>.
 * `Link by Mirror`
 	* Link multiple modules of the same prototype by mirror.
 	* Only available when one or more <b>homogenous modules</b> are selected (same prototype)
 * `Unlink Mirrors`
 	* Unlink mirrors from all selected modules.
 	* Only available <b>when one or more modules are selected</b>.
 * `List Mirrors`
 	* List mirror links of one selected module.
 	* Only available <b>when exactly one module is selected</b>.
 * `Select Network`
 	* Selects the network parent object (arrow axes) the selected module(s) belong to.
 * `Sever Network`
 	* Sever one network into two at the specific point.
 	* Only available <b>when exactly two neighbouring modules are selected</b>.
 * `Join Network`
 	* Join two compatible networks; deletes the network that becomes empty.
 	* Only available <b>when exactly two modules from different networks are selected</b>. In addition, they must also be compatible (both connectivity- and chain-occupancy- wise).
 * `Select Mirror`
 	* Selects all mirror-linked modules of the selected module(s).
 	* Only available <b>when more than zero modules are selected</b>.
 * `Add Joint`
 	* Add a path guide joint
 	* Only available <b>when the selection does not contain joints</b>.
 * `Extrude Joint`
 	* Extrude a path guide joint from another.
 	* Only available <b>when the selection only contains joints</b>.
 * `Joint to Module`
  	* Move a joint to the COM of a module.
  	* Only available <b>when exactly one module and one joint are selected</b>.


You don't have to type the full name of the module. For example, "extr" will bring up the `Extrude Module` operator.

# Prototype Naming Convention

<p align="center">
<img src="ui_tutorial_names.png" width="70%">
</p>

`Add Module` and `Extrude Module` will prompt you with a filtered list of actionable module names - let's call them <em>filtered prototypes</em>. There could be many modules in a scene, but modules with the same module name (not Blender name) are of the same prototype (like what classes are to objects). For extrusion, prototypes are filtered by compatibility and also terminus occupancy (i.e. is the N and/or C terminus already occupied?).

In the filtered prototype list, you will see that the name of a module is bounded by two period marks. These marks are sentinels which makes it easy to search the exact module one is looking for. Try typing just `D4` in `Add Module`, and see what happens when you type `.D4` or `D4.` or `.D4.`.

The first letter, if there is one, denotes the <b>C Terminus</b> chain ID of the extrusion. This is needed because hub modules have more than one chain to extrude to and from.

The last letter is therefore the <b>N Terminus</b> chain ID in the to-be-extruded module.

# Coloring
The colour of each newly added module is set randomly. If you wish to set them manually, you can open the left-hand-side panel (via <kbd>t</kbd>) to adjust the color when the operator is <em>active</em> (when you've selected it after typing it). It's highly recommended that you change the color while the prototype selection is set to the `-Change Color-` placeholder. This is because with each color change Blender removes the object it added and re-adds it with a different color. That can cause considerable lag if you drag the colour sampler around the palette. You can also go into the material of the module object on the right-most side panel when the operator options are gone.

# Mirror-Linking
Mirror-linking was originally implemented to enforce symmetric execution of extrusion or deletion on the arms of a symmetric hub. I thought this could be potentially useful for manual design so I've made this available to the user via operators.

Mirror-linked modules essentially share extrusion and deletion operations. That means if you select just one of a mirror-linked group of modules and do extrusion on it, all other mirror-linked modules will also receive the same operation

# Useful Blender shortcuts:
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

# Collision Detection
By default collision detection is done on extrusion and placement of modules. The calculation is not perfect because we're using single module 3D models instead of their true atomic representation. If for any reason you need to disable this, you can find the tickbox in the left-hand-side panel (toggle by <kbd>t</kbd>).