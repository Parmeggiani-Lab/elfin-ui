import re
import colorsys
import random
import json
import time
from collections import OrderedDict

import bpy
import bmesh
import mathutils
from bpy.app.handlers import persistent
import mathutils.bvhtree
from . import addon_paths

blender_pymol_unit_conversion = 10.0

class ColorWheel(object):
    hue_diff = 0.3
    lightness_base = 0.3
    lightness_variance = 0.3
    saturation_base = 0.8
    saturation_variance = .2
    def __init__(self):
        self.hue = random.random()
    
    def next_color(self, ):
        self.hue += (self.hue_diff / 2) + random.random() * (1 - self.hue_diff)
        lightness = self.lightness_base + \
            random.random() * self.lightness_variance
        saturation = self.saturation_base + \
            random.random() * self.saturation_variance
        return colorsys.hls_to_rgb(
            self.hue % 1.0, 
            lightness % 1.0, 
            saturation % 1.0
        )

color_wheel = ColorWheel()

def get_xdb():
    return bpy.context.scene.elfin.xdb

def suitable_for_extrusion(context):
    n_objs = len(context.selected_objects)
    if n_objs == 0:
        return False

    if context.selected_objects[0].mode != 'OBJECT':
        return False

    if n_objs == 1:
        return True
    elif n_objs > 1:
        first_mod_name = context.selected_objects[0].elfin.module_name
        for i in range(1, n_objs):
            if context.selected_objects[i].elfin.module_name != first_mod_name:
                return False
        return True

def give_module_new_color(mod, new_color=None):
    mat = bpy.data.materials.new(name='mat_' + mod.name)
    mat.diffuse_color = new_color if new_color else color_wheel.next_color()
    mod.data.materials.append(mat)
    mod.active_material = mat

def show_links(obj=None):
    if obj:
        obj.elfin.show_links()
    elif bpy.context.selected_objects:
        bpy.context.selected_objects[0].elfin.show_links()

def get_selected():
    """
    Return the first selected object, or None if nothing is selected.
    """
    if len(bpy.context.selected_objects):
        return bpy.context.selected_objects[0]
    else:
        return None

def delete_if_overlap(mod_obj, obj_list=None):
    """
    Delete a mod_obj if it overlaps with any object in obj_list.

    This function is conditioned on the disable_collision_check toggle.
    """

    # Update must be called first because operations like extrude will first
    # transform the object.
    if not bpy.context.scene.elfin.disable_collision_check:
        bpy.context.scene.update()
        if check_module_overlap(mod_obj, obj_list=obj_list):
            delete_object(mod_obj)
            return True
    return False

def delete_object(obj):
    """Delete an object using default delete operator while preserving
    selection before deletion.
    """
    # Cache selection
    selection = bpy.context.selected_objects[:]
    object_name = obj.name

    obj.elfin.sever_links()

    bpy.ops.object.select_all(action='DESELECT')
    obj.hide = False
    obj.select = True
    bpy.ops.object.delete(use_global=False)
    
    # Restore selection
    for ob in selection:
        if ob != obj:
            ob.select = True

def check_module_overlap(mod_obj, obj_list=None, scale_factor=0.85):
    """
    Tests whether an object's mesh overlaps with any mesh in obj_list.

    Args: 
     - mod_obj - the object under test.
     - obj_list - optional; the list of objects to test against.
     - scale_factor - optional; the scale to apply before testing.

    Returns:
     - bool - whether or not a collision (overlap) was found.
    """
    if not obj_list:
        obj_list = bpy.context.scene.objects
    scale = mathutils.Matrix.Scale(scale_factor, 4)

    mod_bm = bmesh.new()
    mod_bm.from_mesh(mod_obj.data)
    mod_bm.transform(mod_obj.matrix_world * scale)
    mod_bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(mod_bm)
    for ob in obj_list:
        if ob == mod_obj:
            continue

        ob_bm = bmesh.new()
        ob_bm.from_mesh(ob.data)
        ob_bm.transform(ob.matrix_world * scale)
        ob_bvh_tree = mathutils.bvhtree.BVHTree.FromBMesh(ob_bm)

        overlaps = mod_bvh_tree.overlap(ob_bvh_tree)

        if len(overlaps) > 0:
            return True

    return False

def raise_frame(moving_mod, rel, fixed_mod=None):
    rot = mathutils.Matrix(rel['rot'])
    rot.transpose()
    transform_object(
        obj=moving_mod, 
        rot=rot, 
        tran_before=[-t/blender_pymol_unit_conversion for t in rel['tran']]
    )
    # Equalize frame
    if fixed_mod != None:
        transform_object(
            obj=moving_mod, 
            rot=fixed_mod.rotation_euler.to_matrix(),
            tran_after=fixed_mod.location
        )

def drop_frame(moving_mod, rel, fixed_mod=None):
    transform_object(
        obj=moving_mod, 
        rot=rel['rot'], 
        tran_after=[t/blender_pymol_unit_conversion for t in rel['tran']]
    )
    # Equalize frame
    if fixed_mod != None:
        transform_object(
            obj=moving_mod, 
            rot=fixed_mod.rotation_euler.to_matrix(),
            tran_after=fixed_mod.location
        )

def transform_object(
        obj, 
        tran_before=[0,0,0],
        rot=[[1,0,0],[0,1,0],[0,0,1]],
        tran_after=[0,0,0]
    ):
    """
    Transforms an object with the given translation vetors and rotation matrix.
    """
    tran_before_vec = mathutils.Vector(tran_before)
    rot_mat = mathutils.Matrix(rot)
    tran_after_vec = mathutils.Vector(tran_after)

    obj.location = (rot_mat * (obj.location + tran_before_vec)) + tran_after_vec

    # rotation around object center
    obj.rotation_euler = \
        (rot_mat * obj.rotation_euler.to_matrix()).to_euler()

def get_compatible_hub_components(hub_name, terminus, single_name):
    terminus = terminus.lower()
    assert(terminus in {'c', 'n'})

    comp_data = bpy.context.scene.elfin.xdb \
                ['hub_data'][hub_name]['component_data']

    component_names = []
    for comp_name in comp_data:
        if single_name in comp_data \
            [comp_name][terminus+'_connections'].keys():
            component_names.append(comp_name)
    return component_names

def module_enum_tuple(mod_name, extrude_from=None, extrude_into=None, direction=None):
    """Creates an enum tuple storing the single module selector, prefixed or
    suffixed by the terminus of a hub from/to which the single module is
    extruded.
    """
    if direction is not None:
        direction = direction.lower()
        assert(direction in {'n', 'c'})
        assert(extrude_from is not None)
        if extrude_into is None:
            extrude_into = ''

    if direction == 'c':
        mod_sel = '.'.join([extrude_from, mod_name, extrude_into])
    elif direction == 'n':
        mod_sel = '.'.join([extrude_into, mod_name, extrude_from])
    else:
        mod_sel = '.'.join(['', mod_name, ''])

    return (mod_sel, mod_sel, '')

def load_xdb():
    with open(addon_paths.xdb_path, 'r') as file:
        xdb = OrderedDict(json.load(file))
    print('Xdb loaded')
    return xdb

def load_module_library():
    with bpy.types.BlendDataLibraries.load(addon_paths.modlib_path) as (data_from, data_to):
        lib = data_from.objects
    print('Module library loaded')
    return lib

def link_module(module_name):
    """Links a module module from library.blend. Supports all module types."""
    try:
        with bpy.data.libraries.load(addon_paths.modlib_path) as (data_from, data_to):
            data_to.objects = [module_name]

        linked_module = bpy.context.scene.objects.link(data_to.objects[0]).object
        linked_module.elfin.module_name = module_name

        xdb = bpy.context.scene.elfin.xdb
        single_xdata = xdb['single_data'].get(module_name, None)
        if single_xdata:
            linked_module.elfin.module_type = 'single'
        else:
            hub_xdata = xdb['hub_data'].get(module_name, None)
            if hub_xdata:
                linked_module.elfin.module_type = 'hub'
            else:
                print('Warning: user is trying to link a module that is neither single or hub type')
                single_a_name, single_b_name = module_name.split['-']
                double_xdata = xdb['double_data'].get(
                    single_a_name, {}).get(
                    single_b_name, None)
                if double_xdata:
                    linked_module.elfin.module_type = 'double'
                else:
                    raise ValueError('Module name not found in xdb: ', mod_name)

        linked_module.elfin.is_module = True
        linked_module.elfin.self_object = linked_module

        return linked_module
    except Exception as e:
        if linked_module:
            delete_object(linked_module)
        raise e
