
# Installing elfin-ui

Download elfin-ui and install it using the following commands:

```
git clone git@github.com:joy13975/elfin-ui
cd elfin-ui
./install
```

Make sure to select v2.79 when asked by the script.

<p align="center">
<img src="1_download_and_install.png" width="85%">
</p>

# Enabling elfin-ui

Enable the addon in Blender's user preferences (`File` > `User Preferences` > `Add-ons`). Search for `elfin` and after ticking the box make sure to hit the `Save User Preferences` button.

Before enabling, your Blender probably looks like:
<p align="center">
<img src="2_before_blender_prefs.png" width="85%">
</p>

After enabling, your Blender should look like:
<p align="center">
<img src="2_after_blender_prefs.png" width="85%">
</p>

Notice that the left-hand-side panel now has an `elfin` section with some debug buttons. You don't need to touch these buttons as they are for debugging. You might sometimes find a need for disabling collision detection or resetting the properties. There are facilities for processing PyMol-generated .obj module models but for now we don't need to get into that.

# Placing a Module

Move the cursor into Blender's viewport and hit <kbd>space</kbd>. Type in `place` and one item should read `Elfin: Place a module`:

<p align="center">
<img src="3_place_menu.png" width="85%">
</p>

Hit <kbd>enter</kbd> and a prototype list should be displayed:

<p align="center">
<img src="3_place_list.png" width="85%">
</p>

<b>Optional: color setting.</b> Now that the Place operator is activated, you can move your cursor away and set the color for the new module before loading the actual model by using the Operator Properties panel at the bottom-left corner. You don't have to do this because elfin-ui sets a new color randomly for each new module. You <em>can</em> still change the color after loading the model, but if you do that through the Operator Properties panel it will cause lag as Blender removes the model it had loaded and re-loads a new one with a different color. If you've already loaded the model and want to change the color, go into the lower half of the right-hand-side panel, find the `Material` tab (with a copper-colored ball icon) and you can change it there without causing lag.

<p align="center">
<img src="3_place_color.png" width="85%">
</p>

The Operator Properties panel also lets you choose the module prototype to place (this is the same as viewport's prototype list).

<p align="center">
<img src="3_place_panel_list.png" width="85%">
</p>

Select the module prototype you desire. The selected module should get placed at origin in its default orientation:

<p align="center">
<img src="3_place_result.png" width="85%">
</p>

# Extruding from a Module

Again, hit <kbd>space</kbd> with the cursor in Blender's viewport. Type in `ex n` and one item should read `Elfin: Extrude N (add a module to the nterm)`:

<p align="center">
<img src="4_extrude_n_menu.png" width="85%">
</p>

Select the module prototype the same way as with the Place operator. If the terminus being extruded is already occupied by some other module, then this list <em>will be empty</em>. This is important to keep in mind.

<p align="center">
<img src="4_extrude_n_list.png" width="85%">
</p>

Extrusion at the N terminus results in:

<p align="center">
<img src="4_extrude_n_result.png" width="85%">
</p>

# Mirror Linking

Originally designed for enforcing symmetric hubs' arm identiticality, mirror linking cause simultaneous manipulation for two or more separate modules that are not necessarily spatially related.

When modules are <em>mirror-linked</em> (or <em>linked-by-mirror</em>), they are called a group of "mirrors". Any extrusion or deletion applied on any one of the mirrors will also be applied on the rest of the linked mirrors. Further, modules that are a result of extrusion from any mirror will also be automatically mirror-linked (between the new set of modules).

To link modules by mirror, search for `link by`. One item should read `Elfin: Link multiple modules of the same prototype by mirror`:

<p align="center">
<img src="5_link_mirror_menu.png" width="85%">
</p>

As stated, selected modules must be of the same prototype. 

If the linking was successful a message should be shown. If the selected modules already have mirrors linked, you will get a warning and a choice as to whether or not to replace existing links with new ones.

<p align="center">
<img src="5_link_mirror_result.png" width="85%">
</p>

Test Extrusion at N-Term:

<p align="center">
<img src="5_link_mirror_extrude_n.png" width="85%">
</p>

Test Extrusion at C-Term:

<p align="center">
<img src="5_link_mirror_extrude_c.png" width="85%">
</p>

Try deleting one of the extruded modules and see what happens. Revert using <kbd>cmd</kbd>+<kbd>z</kbd> (<kbd>ctrl</kbd> for Windows and Linux).

Mirrors can have any location and rotation - they do not need to be identical. You can even move them (as long as you move the connected modules together) and they will stay linked.

Extruding from symmetric hubs are automatically mirror-linked. 