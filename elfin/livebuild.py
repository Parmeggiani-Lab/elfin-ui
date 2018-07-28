import bpy

from . import addon_paths
from .livebuild_helper import *

# Insert a placeholder as the first option for Place/Extrude operator enums so
# that user can change the color before choosing a module. This makes changing
# display color fast because once a module is selected via the enum, changing
# the displace color causes constant re-linking and that causes lag.
color_change_placeholder = '-Change Color-'
color_change_placeholder_enum_tuple = \
    (color_change_placeholder, color_change_placeholder, '')

class JoinNetworks(bpy.types.Operator):
    bl_idname = 'elfin.join_networks'
    bl_label = 'Join two compatible networks'
    bl_options = {'REGISTER', 'UNDO'}
    ...
    def execute(self, context):
        raise NotImplementedError

class ModuleExtrudeNTerm(bpy.types.Operator):
    bl_idname = 'elfin.module_extrude_nterm'
    bl_label = 'Extrude N (add a module to the nterm)'
    bl_property = "nterm_ext_module"
    bl_options = {'REGISTER', 'UNDO'}

    def modlib_filter_enum_cb(self, context):
        enum_tuples = [color_change_placeholder_enum_tuple]
        if len(context.selected_objects) == 0:
            return enum_tuples

        sel_mod = context.selected_objects[0]
        sel_mod_name = sel_mod.elfin.module_name
        
        hub_xdata = get_hub_module_xdata(sel_mod_name)
        if hub_xdata:
            comp_xdata = hub_xdata['component_data']
            occupied_chains_ids = sel_mod.elfin.n_linkage.keys() + \
                sel_mod.elfin.n_linkage.keys()
            for chain_id, chain_xdata in comp_xdata.items():
                if chain_id in occupied_chains_ids:
                    continue
                for single_name in chain_xdata['n_connections']:
                    enum_tuples.append(
                        module_enum_tuple(
                            single_name, 
                            extrude_from=chain_id, 
                            extrude_into='A',
                            direction='N'))
        else: # Current selected module is a single
            if len(sel_mod.elfin.n_linkage) == 0:
                for single_a_name in context.scene.elfin.xdb['single_data']:
                    if get_double_module_xdata(single_a_name, sel_mod_name):
                        enum_tuples.append(
                            module_enum_tuple(
                                single_a_name,
                                extrude_from='A',
                                extrude_into='A',
                                direction='N'))
                for hub_name in context.scene.elfin.xdb['hub_data']:
                    for hub_comp_name in \
                        get_compatible_hub_components(hub_name, 'C', sel_mod_name):
                        enum_tuples.append(
                            module_enum_tuple(
                                hub_name, 
                                extrude_from='A',
                                extrude_into=hub_comp_name,
                                direction='N'))
        return enum_tuples

    nterm_ext_module = bpy.props.EnumProperty(items=modlib_filter_enum_cb)
    color = bpy.props.FloatVectorProperty(name="Display Color", 
                                        subtype='COLOR', 
                                        default=[0,0,0])

    def execute(self, context):
        if self.nterm_ext_module == color_change_placeholder:
            return {'FINISHED'}

        try:
            xdb = context.scene.elfin.xdb
            selection = context.selected_objects[:]

            # Enum selector format: extrude_into:module_name:extrude_from.
            extrude_into, nterm_mod_name, extrude_from = \
                self.nterm_ext_module.split('.')
            for sel_mod in selection:
                sel_mod_name = sel_mod.elfin.module_name
                ext_mod = link_module(nterm_mod_name)

                print('Extruding module {} (chain {}) from {}\'s N-Term (chain {})'.format(
                    self.nterm_ext_module, extrude_into, sel_mod_name, extrude_from))

                sel_ext_type_pair = (sel_mod.elfin.module_type, ext_mod.elfin.module_type)
                if sel_ext_type_pair == ('single', 'single'):
                    rel = xdb \
                        ['double_data'][nterm_mod_name][sel_mod_name]
                    drop_frame(ext_mod, rel, fixed_mod=sel_mod)
                elif sel_ext_type_pair == ('single', 'hub'):
                    # First drop to hub component frame
                    chain_xdata = xdb \
                        ['hub_data'][nterm_mod_name]\
                        ['component_data'][extrude_into]
                    rel = chain_xdata['c_connections'][sel_mod_name]
                    drop_frame(ext_mod, rel)

                    # Second drop to double B frame
                    rel = xdb \
                        ['double_data'][chain_xdata['single_name']][sel_mod_name]
                    drop_frame(ext_mod, rel, fixed_mod=sel_mod)
                elif sel_ext_type_pair == ('hub', 'single'):
                    chain_xdata = xdb  \
                        ['hub_data'][sel_mod_name] \
                        ['component_data'][extrude_from]
                    rel = chain_xdata['n_connections'][nterm_mod_name]
                    raise_frame(ext_mod, rel, fixed_mod=sel_mod)
                elif sel_ext_type_pair == ('hub', 'hub'):
                    self.report({'ERROR'}, 'Unimplemented')
                    return {'CANCELLED'}
                else:
                    raise ValueError('Invalid sel_ext_type_pair: {}'.format(sel_ext_type_pair))

                give_module_new_color(ext_mod, self.color)
                ext_mod.hide = False # Unhide (default is hidden)

                # Link the modules together
                sel_mod.elfin.new_n_link(extrude_from, ext_mod, extrude_into)
                ext_mod.elfin.new_c_link(extrude_into, sel_mod, extrude_from)

                sel_mod.select = False # Switch single selection to newest module
                ext_mod.select = True

            return {'FINISHED'}
        except Exception as e:
            if ext_mod:
                delete_object(ext_mod)
            raise e

    def invoke(self, context, event):
        self.color = color_wheel.next_color()
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return suitable_for_extrusion(context)

class ModuleExtrudeCTerm(bpy.types.Operator):
    bl_idname = 'elfin.module_extrude_cterm'
    bl_label = 'Extrude C (add a module to the cterm)'
    bl_property = "cterm_ext_module"
    bl_options = {'REGISTER', 'UNDO'}

    def modlib_filter_enum_cb(self, context):
        enum_tuples = [color_change_placeholder_enum_tuple]
        if len(context.selected_objects) == 0:
            return enum_tuples

        sel_mod = context.selected_objects[0]
        sel_mod_name = sel_mod.elfin.module_name

        hub_xdata = get_hub_module_xdata(sel_mod_name)
        if hub_xdata:
            comp_xdata = hub_xdata['component_data']
            occupied_chains_ids = sel_mod.elfin.c_linkage.keys() + \
                sel_mod.elfin.n_linkage.keys()
            for chain_id, chain_xdata in comp_xdata.items():
                if chain_id in occupied_chains_ids:
                    continue
                for single_name in chain_xdata['c_connections']:
                    enum_tuples.append(
                        module_enum_tuple(
                            single_name, 
                            extrude_from=chain_id, 
                            extrude_into='A',
                            direction='C')) 
        else: # Current selected module is a single
            if len(sel_mod.elfin.c_linkage) == 0:
                sel_mod_xdata = context.scene.elfin.xdb['double_data'][sel_mod_name]
                for single_b_name in sel_mod_xdata:
                    enum_tuples.append(
                        module_enum_tuple(
                            single_b_name,
                            extrude_from='A',
                            extrude_into='A',
                            direction='C'))
                for hub_name in context.scene.elfin.xdb['hub_data']:
                    for hub_comp_name in \
                        get_compatible_hub_components(hub_name, 'N', sel_mod_name):
                        enum_tuples.append(
                            module_enum_tuple(
                                hub_name, 
                                extrude_from='A',
                                extrude_into=hub_comp_name,
                                direction='C'))
        return enum_tuples

    cterm_ext_module = bpy.props.EnumProperty(items=modlib_filter_enum_cb)
    color = bpy.props.FloatVectorProperty(name="Display Color", 
                                        subtype='COLOR', 
                                        default=[0,0,0],
                                        options={'LIBRARY_EDITABLE'})

    def execute(self, context):
        if self.cterm_ext_module == color_change_placeholder:
            return {'FINISHED'}

        try:
            xdb = context.scene.elfin.xdb
            selection = context.selected_objects[:]

            # Enum selector format: extrude_from:module_name:extrude_into.
            extrude_from, cterm_mod_name, extrude_into = \
                self.cterm_ext_module.split('.')
            for sel_mod in selection:
                sel_mod_name = sel_mod.elfin.module_name
                ext_mod = link_module(cterm_mod_name)

                print('Extruding module {} (chain {}) from {}\'s C-Term (chain {})'.format(
                    self.cterm_ext_module, extrude_into, sel_mod_name, extrude_from))

                sel_ext_type_pair = (sel_mod.elfin.module_type, ext_mod.elfin.module_type)
                if sel_ext_type_pair == ('single', 'single'):
                    rel = xdb \
                        ['double_data'][sel_mod_name][cterm_mod_name]
                    raise_frame(ext_mod, rel, fixed_mod=sel_mod)
                elif sel_ext_type_pair == ('single', 'hub'):
                    chain_xdata = xdb\
                        ['hub_data'][cterm_mod_name] \
                        ['component_data'][extrude_into]
                    rel = chain_xdata['n_connections'][sel_mod_name]
                    drop_frame(ext_mod, rel, fixed_mod=sel_mod)
                elif sel_ext_type_pair == ('hub', 'single'):
                    chain_xdata = xdb \
                        ['hub_data'][sel_mod_name] \
                        ['component_data'][extrude_from]

                    # First raise to double B frame
                    rel = xdb \
                        ['double_data'][chain_xdata['single_name']][cterm_mod_name]
                    raise_frame(ext_mod, rel)

                    # Second raise to hub component frame
                    rel = chain_xdata['c_connections'][cterm_mod_name]
                    raise_frame(ext_mod, rel, fixed_mod=sel_mod)
                elif sel_ext_type_pair == ('hub', 'hub'):
                    self.report({'ERROR'}, 'Unimplemented')
                    return {'CANCELLED'}
                else:
                    raise ValueError('Invalid sel_ext_type_pair: {}'.format(sel_ext_type_pair))

                give_module_new_color(ext_mod, self.color)
                ext_mod.hide = False # Unhide (default is hidden)

                # Link the modules together
                sel_mod.elfin.new_c_link(extrude_from, ext_mod, extrude_into)
                ext_mod.elfin.new_n_link(extrude_into, sel_mod, extrude_from)

                sel_mod.select = False # Switch single selection to newest module
                ext_mod.select = True

            return {'FINISHED'}
        except Exception as e:
            if ext_mod:
                delete_object(ext_mod)
            raise e

    def invoke(self, context, event):
        self.color = color_wheel.next_color()
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return suitable_for_extrusion(context)

class LoadXdb(bpy.types.Operator):
    bl_idname = 'elfin.load_xdb'
    bl_label = '(Re)load xdb'

    def execute(self, context):
        context.scene.elfin.xdb.clear()
        context.scene.elfin.xdb.update(load_xdb())
        return {'FINISHED'}

class LoadModuleLibrary(bpy.types.Operator):
    bl_idname = 'elfin.load_module_library'
    bl_label = '(Re)load module library'

    def execute(self, context):
        context.scene.elfin.library.clear()
        context.scene.elfin.library.extend(load_module_library())
        return {'FINISHED'}

class PromptMessage(bpy.types.Operator):
    """Elfin Module Collision Message"""
    bl_idname = 'elfin.prompt_message'
    bl_label = 'Prompts a message with an OK button.'
    bl_options = {'REGISTER', 'INTERNAL'}

    title = bpy.props.StringProperty(default='Elfin Message')
    message = bpy.props.StringProperty()
    icon = bpy.props.StringProperty(default='ERROR')

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)
 
    def draw(self, context):
        self.layout.label(self.title)
        row = self.layout.column()
        row.label(self.message, icon=self.icon)

class CheckCollisionAndDelete(bpy.types.Operator):
    bl_idname = 'elfin.check_collision_and_delete'
    bl_label = 'Check collision and delete if positive'

    # Allow keyword specification
    object_name = bpy.props.StringProperty(default='')

    def execute(self, context):
        found_overlap = False

        try:
            ob = bpy.data.objects[self.object_name]
            found_overlap |= delete_if_overlap(ob)
        except KeyError:
            # No valid object_name specified - use selection
            for ob in context.selected_objects:
                if ob.elfin.is_module:
                    found_overlap |= delete_if_overlap(ob)
                else:
                    print('No overlap: {}'.format(ob.name))

        if found_overlap:
            msg = 'Collision was detected and modules were deleted.'
            print(msg)
            bpy.ops.elfin.prompt_message('INVOKE_DEFAULT', \
                message=msg)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.object_name = ''

class PlaceModule(bpy.types.Operator):
    bl_idname = 'elfin.place_module'
    bl_label = 'Place a module'
    bl_property = 'selected_module'
    bl_options = {'REGISTER', 'UNDO'}

    def modlib_enum_cb(self, context):
        res = [color_change_placeholder_enum_tuple]
        for mod in context.scene.elfin.library:
            if not get_double_module_xdata(double_name=mod):
                res.append(module_enum_tuple(mod))
        return res

    selected_module = bpy.props.EnumProperty(items=modlib_enum_cb)
    color = bpy.props.FloatVectorProperty(name="Display Color", 
                                        subtype='COLOR', 
                                        default=[0,0,0])

    def execute(self, context):
        if self.selected_module == color_change_placeholder:
            return {'FINISHED'}

        try:
            print('Placing module {}'.format(self.selected_module))
            
            sel_mod_name = self.selected_module.split('.')[1]
            lmod = link_module(sel_mod_name)

            give_module_new_color(lmod, self.color)
            lmod.hide = False # By default the obj is hidden
            lmod.select = True

            return {'FINISHED'}
        except Exception as e:
            if lmod:
                delete_object(lmod)
            raise e

    def invoke(self, context, event):
        self.color = color_wheel.next_color()
        context.window_manager.invoke_search_popup(self)

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) == 0 or \
            context.selected_objects[0].mode == 'OBJECT'