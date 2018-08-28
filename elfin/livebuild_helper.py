import colorsys
import random
import json
import collections
import functools

import bpy
import bmesh
import mathutils
import mathutils.bvhtree
from . import addon_paths
from .elfin_object_properties import ElfinObjType


# Global (Const) Variables -----------------------

blender_pymol_unit_conversion = 10.0

# Color Change Placeholder
#
#   An option for Place/Extrude operator enums so that user can change the
#   color before choosing a module. This makes changing display color fast
#   because once a module is selected via the enum list, changing the display
#   color causes constant re-linking and that causes lag.
color_change_placeholder = '-Change Color-'
color_change_placeholder_enum_tuple = \
    (color_change_placeholder, color_change_placeholder, '')

# Prototype List Empty Placeholder
#  An option to inform the user that the prototype list is empty
empty_list_placeholder = '-List Empty-'
empty_list_placeholder_enum_tuple = \
    (empty_list_placeholder, empty_list_placeholder, '')

nop_enum_selectors = {
    color_change_placeholder,
    empty_list_placeholder
}

# Classes ----------------------------------------

# Singleton Metaclass
# Credits to https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class LivebuildState(metaclass=Singleton):
    def __init__(self):
        self.n_extrudables = [empty_list_placeholder_enum_tuple]
        self.c_extrudables = [empty_list_placeholder_enum_tuple]
        self.placeables = [empty_list_placeholder_enum_tuple]
        self.load_xdb(update_placeables_too=False)
        self.load_library(update_placeables_too=False)
        self.load_path_guide()
        self.update_placeables()

    def update_extrudables(self, sel_mod):
        self.n_extrudables = get_extrusion_prototype_list(sel_mod, 'n')
        self.c_extrudables = get_extrusion_prototype_list(sel_mod, 'c')

    def update_placeables(self):
        res = [color_change_placeholder_enum_tuple] + \
            [module_enum_tuple(mod_name) for mod_name in self.get_all_module_names()]
        self.placeables = res if len(res) > 1 else [empty_list_placeholder_enum_tuple]

    def get_all_module_names(self):
        groups = (self.xdb['single_data'], self.xdb['hub_data'])
        xdb_mod_names = {k for group in groups for k in group.keys()}
        return [mod_name for mod_name in self.library if mod_name in xdb_mod_names]

    def load_xdb(self, update_placeables_too=True):
        with open(addon_paths.xdb_path, 'r') as file:
            self.xdb = collections.OrderedDict(json.load(file))
        if update_placeables_too:
            self.update_placeables()
        print('{}: Xdb loaded'.format(__class__.__name__))

    def load_library(self, update_placeables_too=True):
        with bpy.types.BlendDataLibraries.load(addon_paths.modlib_path) as (data_from, data_to):
            self.library = data_from.objects
        if update_placeables_too:
            self.update_placeables()
        print('{}: Module library loaded'.format(__class__.__name__))

    def load_path_guide(self):
        with bpy.types.BlendDataLibraries.load(addon_paths.pguide_path) as (data_from, data_to):
            self.pguide = data_from.objects
        print('{}: Path guide library loaded'.format(__class__.__name__))

    def reset(self):
        self.load_xdb()
        self.load_library()
        self.load_path_guide()
        self.update_placeables()

random.seed()
class ColorWheel(metaclass=Singleton):
    hue_diff = 0.14
    lightness_base = 0.4
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

# Decorator for functions that receive a Blender object
class object_receiver:
    """Passes object to func by argument if specified, otherwise use the
    selected object.
    """
    def __init__(self, func):
        self.func = func
        functools.update_wrapper(self, func)

    def __call__(self, obj=None, *args, **kwargs):
        if not obj:
            if get_selection_len() == 0:
                print('No object specified nor selected.')
                return
            return [self.func(obj, *args, **kwargs) for obj in get_selected(-1)]
        else:
            return self.func(obj, *args, **kwargs)

# Quick Access Methods ---------------------------

@object_receiver
def get_mirrors(obj):
    return obj.elfin.mirrors

@object_receiver
def get_elfin(obj):
    return obj.elfin

@object_receiver
def show_links(obj):
    obj.elfin.show_links()

def count_obj():
    return len(bpy.data.objects)

def get_xdb():
    return LivebuildState().xdb

def get_selection_len():
    return len(bpy.context.selected_objects)

def get_selected(n=1):
    """
    Return the first n selected object, or None if nothing is selected.
    """
    if get_selection_len():
        selection = bpy.context.selected_objects
        if n == 1:
            return selection[0]
        elif n == -1:
            return selection[:]
        else:
            return selection[:n]
    else:
        return []

# Helpers ----------------------------------------

def move_to_new_network(mod):
    """Move all modules on the same network as mod under a new network parent
    object.
    """
    new_network = create_network('module')

    # Gather all modules into a list and calculate COM
    com = mathutils.Vector([0, 0, 0])
    modules = []
    for m in walk_network(mod):
        modules.append(m)
        com += m.matrix_world.translation

    com = com / len(modules)
    new_network.location = com
    new_network.rotation_euler = mod.parent.rotation_euler.copy()
    bpy.context.scene.update() # Mandatory update to reflect new parent transform
    for m in modules:
        mw = m.matrix_world.copy()
        m.parent = new_network
        m.matrix_world = mw

def create_network(network_type):
    """Creates and returns a new arrow object as a network parent object, preserving
    selection.
    """
    selection = get_selected(-1)
    for s in selection: s.select = False

    bpy.ops.object.empty_add(type='ARROWS')
    nw = get_selected()
    nw.select = False
    nw.elfin.init_network(nw, network_type)

    for s in selection:s.select = True

    return nw

def check_network_integrity(network):
    """Returns the network (list of modules) consists of a single network and
    is spatially well formed, meaning all interfaces of the network must be
    the way they were found by elfin as elfin had placed them via extrusion.
    Network level transformations should not destroy well-formed-ness.
    """
    ... # Currently not needed
    return NotImplementedError

def import_joint():
    """Links a bridge object and initializes it using two end joints."""
    joint = None
    try:
        with bpy.data.libraries.load(addon_paths.pguide_path) as (data_from, data_to):
            data_to.objects = ['joint']

        joint = bpy.context.scene.objects.link(data_to.objects[0]).object
        joint.elfin.init_joint(joint)

        return joint
    except Exception as e:
        if joint: 
            # In case something went wrong before this line in try
            joint.elfin.obj_ptr = joint
            joint.elfin.destroy()
        raise e

def import_bridge(joint_a, joint_b):
    """Links a bridge object and initializes it using two end joints."""
    bridge = None
    try:
        with bpy.data.libraries.load(addon_paths.pguide_path) as (data_from, data_to):
            data_to.objects = ['bridge']

        bridge = bpy.context.scene.objects.link(data_to.objects[0]).object
        bridge.elfin.init_bridge(bridge, joint_a, joint_b)

        return bridge
    except Exception as e:
        if bridge: 
            # In case something went wrong before this line in try
            bridge.elfin.obj_ptr = bridge
            bridge.elfin.destroy()
        raise e

def module_menu(self, context): 
    self.layout.menu("INFO_MT_elfin_add", icon="PLUGIN")

def walk_network(module_obj, entering_chain=None, entering_side=None):
    """A generator that traverses the module network depth-first and yields each object on the
    way.
    """

    yield module_obj

    # Walk n-terminus first
    for n_obj in module_obj.elfin.n_linkage:
        if not (entering_side == 'c' and entering_chain == n_obj.source_chain_id):
            yield from walk_network(
                module_obj=n_obj.target_mod, 
                entering_chain=n_obj.target_chain_id,
                entering_side='n')

    # Then c-terminus
    for c_obj in module_obj.elfin.c_linkage:
        if not (entering_side == 'n' and entering_chain == c_obj.source_chain_id):
            yield from walk_network(
                module_obj=c_obj.target_mod, 
                entering_chain=c_obj.target_chain_id,
                entering_side='c')

def extrude_terminus(which_term, selector, sel_mod, color):
    """Extrudes selector module at the which_term of sel_mod"""
    assert which_term in {'n', 'c'}

    ext_mod = None
    try:
        sel_mod_name = sel_mod.elfin.module_name
        sel_mod.select = False

        # Extract chain IDs and module name
        c_chain, ext_mod_name, n_chain = \
            selector.split('.')
        ext_mod = import_module(ext_mod_name)
        extrude_from = n_chain if which_term == 'n' else c_chain
        extrude_into = c_chain if which_term == 'n' else n_chain
        sel_ext_type_pair = (sel_mod.elfin.module_type, ext_mod.elfin.module_type)

        print(('Extruding module {to_mod} (chain {to_chain})'
            ' from {from_mod}\'s {terminus}-Term (chain {from_chain})').format(
            to_mod=selector, 
            to_chain=extrude_into,
            from_mod=sel_mod_name,
            terminus=which_term.upper(),
            from_chain=extrude_from))

        def _extrude(fixed_mod, ext_mod, src_chain=extrude_from):
            tx = get_tx(
                fixed_mod, 
                src_chain,
                extrude_into,
                ext_mod, 
                which_term, 
                sel_ext_type_pair
                )
            ext_mod.matrix_world = tx * ext_mod.matrix_world

            # touch up
            bpy.context.scene.update() # Udpate to get the correct matrices
            ext_mod.parent = fixed_mod.parent # Same network

            give_module_new_color(ext_mod, color)
            ext_mod.hide = False # Unhide (default is hidden)
            if which_term == 'n':
                fixed_mod.elfin.new_n_link(src_chain, ext_mod, extrude_into)
                ext_mod.elfin.new_c_link(extrude_into, fixed_mod, src_chain)
            else:
                fixed_mod.elfin.new_c_link(src_chain, ext_mod, extrude_into)
                ext_mod.elfin.new_n_link(extrude_into, fixed_mod, src_chain)
            ext_mod.select = True

            return [ext_mod] # for mirror linking


        xdb = get_xdb()
        if sel_ext_type_pair in {('single', 'single'), ('single', 'hub')}:
            _extrude(sel_mod, ext_mod)

            if sel_mod.elfin.mirrors:
                create_module_mirrors(
                    sel_mod, 
                    [ext_mod], 
                    ext_mod_name, 
                    _extrude)
        elif sel_ext_type_pair == ('hub', 'single'):
            #
            # Extrude from hub to single.
            #
            hub_xdata = xdb['hub_data'][sel_mod_name]
            def extrude_hub_single(sel_mod, new_mod):
                _extrude(sel_mod, new_mod, src_chain=extrude_from)

                if hub_xdata['symmetric']:
                    # Calculate non-occupied chain IDs
                    hub_all_chains = set(hub_xdata['component_data'].keys())
                    if which_term == 'n':
                        hub_busy_chains = set(sel_mod.elfin.n_linkage.keys()) 
                    else:
                        hub_busy_chains = set(sel_mod.elfin.c_linkage.keys())
                    hub_free_chains = hub_all_chains - hub_busy_chains
                       
                    mirrors = [new_mod]
                    for src_chain_id in hub_free_chains:
                        mirror_mod = import_module(ext_mod_name)
                        mirror_mod.parent = sel_mod.parent # Same network
                        _extrude(sel_mod, mirror_mod, src_chain_id)
                        mirrors.append(mirror_mod)

                    for m in mirrors:
                        m.elfin.mirrors = mirrors

                    return mirrors # Mirrers are taken care of here already
                else:
                    return [new_mod]

            first_mirror_group = extrude_hub_single(sel_mod, ext_mod)

            if sel_mod.elfin.mirrors:
                create_module_mirrors(
                    sel_mod,
                    first_mirror_group,
                    ext_mod_name,
                    extrude_hub_single)
        elif sel_ext_type_pair == ('hub', 'hub'):
            #
            # Extrude from hub to hub is NOT allowed.
            #
            raise NotImplementedError
        else:
            raise ValueError('Invalid sel_ext_type_pair: {}'.format(sel_ext_type_pair))

        return {'FINISHED'}
    except Exception as e:
        if ext_mod:
            # In case something went wrong before this line in try
            ext_mod.elfin.obj_ptr = ext_mod
            ext_mod.elfin.destroy()
        sel_mod.select = True # Restore selection
        raise e
    return {'FINISHED'}

def execute_extrusion(which_term, selector, color):
    """Executes extrusion respecting mirror links and filers mirror selections
    """
    if selector in nop_enum_selectors: return

    filter_mirror_selection()
    for sel_mod in get_selected(-1): 
        extrude_terminus(which_term, selector, sel_mod, color)

def get_extrusion_prototype_list(sel_mod, which_term):
    """Generates a prototype list appropriately filtered for extrusion.
    """
    assert which_term in {'n', 'c'}

    enum_tuples = [color_change_placeholder_enum_tuple]

    # Selection length is guranteed by poll()
    sel_mod_name = sel_mod.elfin.module_name
    sel_mod_type = sel_mod.elfin.module_type

    xdb = get_xdb()
    if sel_mod_type == 'hub':
        hub_xdata = xdb['hub_data'][sel_mod_name]
        if which_term == 'n':
            occupied_termini = sel_mod.elfin.n_linkage.keys()
            conn_name = 'n_connections'
        else:
            occupied_termini = sel_mod.elfin.c_linkage.keys()
            conn_name = 'c_connections'

        for chain_id, chain_xdata in hub_xdata['component_data'].items():
            if chain_id in occupied_termini: continue

            for single_name in chain_xdata[conn_name]:
                enum_tuples.append(
                    module_enum_tuple(
                        single_name, 
                        extrude_from=chain_id, 
                        extrude_into='A',
                        direction=which_term))

            # Only allow one chain to be extruded because other
            # "mirrors" will be generated automatically
            if hub_xdata['symmetric']: break
    elif sel_mod_type == 'single':
        # Checks for occupancy by counting n/c termini links
        if which_term == 'n':
            link_len = len(sel_mod.elfin.n_linkage)
        else:
            link_len = len(sel_mod.elfin.c_linkage)

        if link_len == 0:
            if which_term == 'n':
                name_gen = (single_a_name \
                    for single_a_name in xdb['single_data'] \
                    if sel_mod_name in xdb['double_data'][single_a_name])
            else:
                name_gen = (single_b_name \
                    for single_b_name in xdb['double_data'][sel_mod_name])

            for single_name in name_gen:
                    enum_tuples.append(
                        module_enum_tuple(
                            single_name,
                            extrude_from='A',
                            extrude_into='A',
                            direction=which_term))

            for hub_name in xdb['hub_data']:
                # Logically one can never extrude a symmetric hub
                # See README development notes
                if xdb['hub_data'][hub_name]['symmetric']: continue

                compatible_hub_comps = \
                    get_compatible_hub_components(
                        hub_name, 
                        'c' if which_term == 'n' else 'n', 
                        sel_mod_name)
                for hub_comp_name in compatible_hub_comps:
                    enum_tuples.append(
                        module_enum_tuple(
                            hub_name, 
                            extrude_from='A',
                            extrude_into=hub_comp_name,
                            direction=which_term))
    else:
        raise ValueError('Unknown module type: ', sel_mod_type)

    # Remove color change placeholder if nothing can be extruded
    return enum_tuples if len(enum_tuples) > 1 else []

def get_tx(
    fixed_mod, 
    extrude_from,
    extrude_into,
    ext_mod, 
    which_term, 
    rel_type
    ):
    """Returns the transformation matrix for when ext_mod is extruded from
    fixed_mod's which_term.
    """
    assert which_term in {'n', 'c'}

    fixed_mod_name = fixed_mod.elfin.module_name
    ext_mod_name = ext_mod.elfin.module_name
    xdb = get_xdb()

    if rel_type == ('single', 'single'):

        if which_term == 'n':
            rel = xdb['double_data'][ext_mod_name][fixed_mod_name]
            return get_drop_frame_transform(rel['rot'], rel['tran'], fixed_mod)
        else:
            rel = xdb['double_data'][fixed_mod_name][ext_mod_name]
            return get_raise_frame_transform(rel['rot'], rel['tran'], fixed_mod)

    elif rel_type == ('single', 'hub'):

        chain_xdata = xdb['hub_data'][ext_mod_name]['component_data'][extrude_into]
        if which_term == 'n':
            rel = chain_xdata['c_connections'][fixed_mod_name]
            # First drop to hub component frame
            tx1 = get_drop_frame_transform(rel['rot'], rel['tran'])

            rel = xdb['double_data'][chain_xdata['single_name']][fixed_mod_name]
            # Second drop to double B frame
            tx2 = get_drop_frame_transform(rel['rot'], rel['tran'], fixed_mod)

            return tx2 * tx1
        else:
            rel = chain_xdata['n_connections'][fixed_mod_name]
            return get_drop_frame_transform(rel['rot'], rel['tran'], fixed_mod)

    elif rel_type == ('hub', 'single'):

        chain_xdata = xdb['hub_data'][fixed_mod_name]['component_data'][extrude_from]
        if which_term == 'n':
            rel = chain_xdata['n_connections'][ext_mod_name]
            return get_raise_frame_transform(rel['rot'], rel['tran'], fixed_mod)
        else:
            # First raise to double B frame
            rel = xdb['double_data'] \
                [chain_xdata['single_name']][ext_mod_name]
            tx1 = get_raise_frame_transform(rel['rot'], rel['tran'])

            # Second raise to hub component frame
            rel = chain_xdata['c_connections'][ext_mod_name]
            tx2 = get_raise_frame_transform(rel['rot'], rel['tran'], fixed_mod)

            return tx2 * tx1

def unlink_mirror(modules=None):
    mods = modules[:] if modules else bpy.context.selected_objects[:]
    if not mods: return
    for m in mods: 
        m.elfin.mirrors = None

def link_by_mirror(modules=None):
    mirrors = modules[:] if modules else bpy.context.selected_objects[:]
    if not mirrors: return
    m0 = mirrors[0]
    for i in range(1, len(mirrors)):
        if mirrors[i].elfin.module_name != m0.elfin.module_name:
            print('Error: selected modules are not of the same prototype')
            return
    for m in mirrors:
        m.elfin.mirrors = mirrors[:]

def create_module_mirrors(
    root_mod, 
    new_mirrors, 
    link_mod_name,
    extrude_func):
    for m in root_mod.elfin.mirrors:
        if m != root_mod:
            mirror_mod = import_module(link_mod_name)
            mirror_mod.parent = m.parent # same parent as m
            to_be_mirrored = extrude_func(m, mirror_mod)
            for tbm in to_be_mirrored:
                new_mirrors.append(tbm)

    for m in new_mirrors:
        m.elfin.mirrors = new_mirrors

def filter_mirror_selection():
    for s in bpy.context.selected_objects:
        if s.select and s.elfin.mirrors:
            for m in s.elfin.mirrors:
                # Note that m could be the next s!
                if m and m != s: m.select = False

def suitable_for_extrusion(context):
    """Checks selection is not none and is homogenous.
    """
    selection = context.selected_objects
    n_objs = len(selection)
    if n_objs == 0:
        return False

    # In object mode?
    if selection[0].mode != 'OBJECT':
        return False

    # Homogenous?
    first_mod_name = selection[0].elfin.module_name
    for o in selection:
        if not o.elfin.is_module() or o.elfin.module_name != first_mod_name:
            return False
    return True

def give_module_new_color(mod, new_color=None):
    mat = bpy.data.materials.new(name='mat_' + mod.name)
    mat.diffuse_color = new_color if new_color else ColorWheel().next_color()
    mod.data.materials.append(mat)
    mod.active_material = mat

def delete_if_overlap(obj, obj_list=None):
    """
    Delete obj if it is a module and it overlaps with any object in obj_list.

    This function is conditioned on the disable_collision_check toggle.
    """

    # Update must be called first because operations like extrude will first
    # transform the object.
    if not bpy.context.scene.elfin.disable_collision_check:
        bpy.context.scene.update()
        if obj.elfin.is_module() and check_module_overlap(obj, obj_list=obj_list):
            obj.elfin.destroy()
            return True
    return False

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

def get_raise_frame_transform(rel_rot, rel_tran, fixed_mod=None):
    rtp = []
    rot = mathutils.Matrix(rel_rot)
    rot.transpose()
    rtp.append((None, [-t/blender_pymol_unit_conversion for t in rel_tran]))
    rtp.append((rot, None))
    # Equalize frame
    if fixed_mod != None:
        rtp.append((fixed_mod.rotation_euler.to_matrix(), fixed_mod.location))
    return stack_transforms(rtp)

def get_drop_frame_transform(rel_rot, rel_tran, fixed_mod=None):
    rtp = []
    rtp.append((rel_rot, [t/blender_pymol_unit_conversion for t in rel_tran]))
    # Equalize frame
    if fixed_mod != None:
        rtp.append((fixed_mod.rotation_euler.to_matrix(), fixed_mod.location))
    return stack_transforms(rtp)

def stack_transforms(rt_pairs):
    tx = mathutils.Matrix()
    for rt in rt_pairs:
        if rt[0]: tx = mathutils.Matrix(rt[0]).to_4x4() * tx
        if rt[1]: tx = mathutils.Matrix.Translation(rt[1]) * tx

    return tx

# Deprecated
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

def get_compatible_hub_components(hub_name, which_term, single_name):
    assert which_term in {'n', 'c'}

    comp_data = LivebuildState().xdb \
                ['hub_data'][hub_name]['component_data']

    component_names = []
    for comp_name in comp_data:
        if single_name in comp_data \
            [comp_name][which_term+'_connections'].keys():
            component_names.append(comp_name)
    return component_names

def module_enum_tuple(mod_name, extrude_from=None, extrude_into=None, direction=None):
    """Creates an enum tuple storing the single module selector, prefixed or
    suffixed by the terminus of a hub from/to which the single module is
    extruded.

    Enum selector format: C-Chain ID, Module, N-Chain ID

    Example context:    
        Let module A receive an extrusion opereation which attempts to add B
        to A's n-terminus. 
    args:
     - mod_name: module B's name.
     - extrude_from: module A's chain ID that is receiving extrusion.
     - extrude_into: module B's chain ID that is complementing the extrusion.
     - direction: is B being added to A's c-terminus or n-terminus.

    """
    if direction is not None:
        assert direction in {'n', 'c'}
        assert extrude_from is not None
        if extrude_into is None:
            extrude_into = ''

    # Keep the selector format: n_chain, mod, c_chain
    if direction == 'c':
        mod_sel = '.'.join([extrude_from, mod_name, extrude_into])
        display = ':{}(C) -> (N){}:{}.'.format(extrude_from, extrude_into, mod_name)
    elif direction == 'n':
        mod_sel = '.'.join([extrude_into, mod_name, extrude_from])
        display = ':{}(N) -> (C){}:{}.'.format(extrude_from, extrude_into, mod_name)
    else:
        mod_sel = '.'.join(['', mod_name, ''])
        display = mod_sel

    return (mod_sel, display, '')

def import_module(mod_name):
    """Links a module object from library.blend. Supports all module types."""
    lmod = None
    try:
        with bpy.data.libraries.load(addon_paths.modlib_path) as (data_from, data_to):
            data_to.objects = [mod_name]

        lmod = bpy.context.scene.objects.link(data_to.objects[0]).object

        lmod.elfin.init_module(lmod, mod_name)

        return lmod
    except Exception as e:
        if lmod: 
            # In case something went wrong before this line in try
            lmod.elfin.obj_ptr = lmod
            lmod.elfin.destroy()
        raise e
