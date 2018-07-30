#
# Elfin's GUI Front-end as a Blender addon
# 
# Author: Joy Yeh 
# Email: joyyeh.tw@gmail.com
#

# Addon design notes
#   * Each separate object is a separate chain
#   * There should be no faces in any design spec object
#       * Code simply ignores faces
#       x Provide a face delete operator 
#   * There should be no discontinuities in an object
#       * Code should verify this
#   x Unit conversion: 1 blender unit is 10 A, or 1 nm
#       x 1 blender unit === 10 pymol units
#   * Module avatar generation:
#       * How to do avatars in viewport elegantly? 
#           * Use links so none of the models can be edited
#

bl_info = {'name': 'Elfin UI', 'category': 'Elfin'}

import sys
import importlib
import re
import os

# Dyanmic import and reload ----------------------

print('--------------------- Elfin UI Addon import/reload')

modules_to_import = [ 
    'addon_paths',
    'debug',
    'livebuild_helper',
    'livebuild', 
    'obj_processor',
    'module_lifetime_watcher'
]
root_module = sys.modules[__name__]

for mod in modules_to_import:
    # Support 'reload' case.
    if mod in locals():
        importlib.reload(getattr(root_module, mod))
        print('Reloaded ', mod)
    else:
        setattr(root_module, mod, importlib.import_module('.' + mod, 'elfin'))
        print('Imported ', mod)

import bpy
from bpy.app.handlers import persistent

from .elfin_properties import ElfinProperties

# Master PropertyGroup ---------------------------

class ElfinSceneProperties(ElfinProperties):
    """Elfin's Scene property catcher class"""
    @property
    def xdb(self):
        if '_xdb' not in self.keys():
            self['_xdb'] = livebuild_helper.load_xdb()
        return self['_xdb']

    @property
    def library(self):
        if '_library' not in self.keys():
            self['_library'] = livebuild_helper.load_module_library()
        return self['_library']

    pp_src_dir = bpy.props.StringProperty(
        subtype='DIR_PATH', 
        default='obj_aligned')
    pp_dst_dir = bpy.props.StringProperty(
        subtype='FILE_PATH', 
        default='module_library.blend')
    pp_decimate_ratio = bpy.props.FloatProperty(default=0.15, min=0.00, max=1.00)
    disable_collision_check = bpy.props.BoolProperty(default=False)

    def reset(self):
        self['_xdb'] = livebuild_helper.load_xdb()
        self['_library'] = livebuild_helper.load_module_library()
        self.property_unset('pp_src_dir')
        self.property_unset('pp_dst_dir')
        self.property_unset('pp_decimate_ratio')
        self.property_unset('disable_collision_check')

class LinkageProperty(bpy.types.PropertyGroup):
    target_mod = bpy.props.PointerProperty(type=bpy.types.Object)
    target_chain_id = bpy.props.StringProperty()

class ElfinObjectProperties(ElfinProperties):
    """Elfin's Object property catcher class"""
    
    is_module = bpy.props.BoolProperty(default=False)
    module_name = bpy.props.StringProperty()
    module_type = bpy.props.StringProperty()
    self_object = bpy.props.PointerProperty(type=bpy.types.Object)

    c_linkage = \
        bpy.props.CollectionProperty(type=LinkageProperty)
    n_linkage = \
        bpy.props.CollectionProperty(type=LinkageProperty)

    def new_c_link(self, source_chain_id, target_mod, target_chain_id):
        link = self.c_linkage.add()
        link.name = source_chain_id
        link.target_mod = target_mod
        link.target_chain_id = target_chain_id

    def new_n_link(self, source_chain_id, target_mod, target_chain_id):
        link = self.n_linkage.add()
        link.name = source_chain_id
        link.target_mod = target_mod
        link.target_chain_id = target_chain_id

    def show_links(self):
        print('Links of {}'.format(self.self_object.name))
        print('C links:')
        for cl in self.c_linkage:
            print(cl.name, cl.target_mod, cl.target_chain_id)
        print('N links:')
        for nl in self.n_linkage:
            print(nl.name, nl.target_mod, nl.target_chain_id)

    def sever_links(self):
        for cl in self.c_linkage:
            if cl.target_mod:
                target_nl = cl.target_mod.elfin.n_linkage
                print('{} severing itself from {}'.format(
                    self.self_object.name, cl.target_chain_id))
                target_nl.remove(target_nl.find(cl.target_chain_id))
        for nl in self.n_linkage:
            if nl.target_mod:
                target_cl = nl.target_mod.elfin.c_linkage
                print('{} severing itself from {}'.format(
                    self.self_object.name, nl.target_chain_id))
                target_cl.remove(target_cl.find(nl.target_chain_id))

    @property
    def mirrors(self):
        return self.get('_mirrors', None)

    @mirrors.setter
    def mirrors(self, value):
        self['_mirrors'] = value

# Panels -----------------------------------------

class ExportPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Export'
    bl_context = 'objectmode'
    bl_category = 'Elfin'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        col = row.column()
        col.operator('elfin.export', text='Export design')

# Operators --------------------------------------

class ExportOperator(bpy.types.Operator):
    bl_idname = 'elfin.export'
    bl_label = 'Export as Elfin input'

    def execute(self, context):
        # Each separate object is a separate chain
        print('Unimplemented')

        return {'FINISHED'}

class DeleteFacesOperator(bpy.types.Operator):
    bl_idname = 'elfin.delete_faces'
    bl_label = 'Delete Faces (selected only)'
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        selObjs = context.selected_objects
        for obj in selObjs:
            context.scene.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.delete(type='ONLY_FACE')
            bpy.ops.object.mode_set(mode='OBJECT')
        return {'FINISHED'}

class ResetOperator(bpy.types.Operator):
    bl_idname = 'elfin.reset'
    bl_label = 'Reset Elfin UI properties'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.scene.elfin.reset()
        return {'FINISHED'}

# Handlers --------------------------------------


def remove_handler(handler_list, handler):
    handler_list[:] = [h for h in handler_list if h is not handler]

def remove_then_add_handler(handler_list, handler):
    """Remove a handler before adding it to prevent duplicates."""
    remove_handler(handler_list, handler)
    handler_list.append(handler)

mod_life_watcher = module_lifetime_watcher.ModuleLifetimeWatcher()
mlw_handler_list = bpy.app.handlers.scene_update_post

@persistent
def remove_watcher(scene):
    remove_handler(mlw_handler_list,
        mod_life_watcher)

@persistent
def add_watcher(scene):
    """Makes a new instance of ModuleLifetimeWatcher and sets that as the new
    watcher globally"""
    global mod_life_watcher
    mod_life_watcher = module_lifetime_watcher.ModuleLifetimeWatcher()
    mlw_handler_list.append(mod_life_watcher)


# Registrations ---------------------------------

def register():
    """Registers properties, and handlers"""
    print('--------------------- Elfin Front Addon register()')
    bpy.utils.register_module(__name__)

    bpy.types.Scene.elfin = bpy.props.PointerProperty(type=ElfinSceneProperties)
    bpy.types.Object.elfin = bpy.props.PointerProperty(type=ElfinObjectProperties)

    # Handlers 

    # Module Lifetime Watcher needs to be unloaded if the current file is
    # getting unloaded. Add the watcher back when new file is loaded so that
    # the watcher initializes correctly on the new already-existing objects in
    # the scene without considering them as new entrances.
    remove_then_add_handler(bpy.app.handlers.load_pre,
        remove_watcher)
    remove_then_add_handler(bpy.app.handlers.load_post,
        add_watcher)

    # Watcher needs to be hooked up in register() as well, because on addon
    # reload the load_pre and load_post handlers won't get called.
    remove_watcher(None)
    add_watcher(None)

    print('--------------------- Elfin Front Addon registered')
    
def unregister():
    """Unregisters properties, and handlers"""
    print('------------------- Elfin Front Addon unregister()')
    bpy.utils.unregister_module(__name__)

    # Also remove any attributes added by Elfin. Blender does not
    # automatically remove them.
    types = [bpy.types.Scene, bpy.types.Object]
    for t in types:
        for k in dir(t):
            if k.startswith('elfin'):
                delattr(t, k)

    # Handlers
    remove_watcher(None)
    remove_handler(bpy.app.handlers.load_pre, \
        remove_watcher)
    remove_handler(bpy.app.handlers.load_post, \
        add_watcher)
                
    print('------------------- Elfin Front Addon unregistered')

if __name__ == '__main__':
    register()
