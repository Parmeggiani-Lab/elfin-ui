import bpy

from . import addon_paths
from .livebuild_helper import *


# Operators --------------------------------------

class ExtrudeJoint(bpy.types.Operator):
    bl_idname = 'elfin.extrude_joint'
    bl_label = 'Extrude a path guide joint'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for joint_a in get_selected(-1):
            loc = [0, 0, 0]
            if get_selection_len() > 0:
                loc = get_selected().location
            
            bridge = link_pguide(pg_type='bridge')
            bridge.location = loc[:]
            
            joint_b = link_pguide(pg_type='joint')
            joint_b.location = loc[:] 
            joint_b.location[1] += 5.0 # This is the y-dimension of bridge

            loc_cons = bridge.constraints.new(type='COPY_LOCATION')
            loc_cons.target = joint_a
            rot_cons = bridge.constraints.new(type='COPY_ROTATION')
            rot_cons.target = joint_a

            stretch_cons = bridge.constraints.new(type='STRETCH_TO')
            stretch_cons.target = joint_b
            stretch_cons.bulge = 0.0

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        if get_selection_len() > 0:
            for s in get_selected(-1):
                if s.elfin.module_type != 'joint':
                    return False
            else:
                return True
        return False

class AddJoint(bpy.types.Operator):
    bl_idname = 'elfin.add_joint'
    bl_label = 'Add a path guide joint'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        loc = [0, 0, 0]
        if get_selection_len() > 0:
            loc = get_selected().location
        
        joint = link_pguide(pg_type='joint')
        joint.location = loc

        return {'FINISHED'}

class SelectMirrors(bpy.types.Operator):
    bl_idname = 'elfin.select_mirrors'
    bl_label = 'Select mirrors (all mirror-linked modules)'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if get_selection_len() > 0:
            for sm in get_selected(n=-1):
                for m in sm.elfin.mirrors:
                    m.select = True
        return {'FINISHED'}

class SelectNetwork(bpy.types.Operator):
    bl_idname = 'elfin.select_network'
    bl_label = 'Select network (all connected modules)'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if get_selection_len() > 0:
            for sm in get_selected(n=-1):
                for o in walk_network(sm):
                    o.select = True
        return {'FINISHED'}

class ListMirrors(bpy.types.Operator):
    bl_idname = 'elfin.list_mirrors'
    bl_label = 'List mirror links of one selected module'
    bl_options = {'REGISTER'}

    def execute(self, context):
        mirrors = get_selected().elfin.mirrors
        mirror_strs = []
        for i in range(len(mirrors)):
            mirror_strs.append('[{}] {}'.format(i, mirrors[i].name))
        MessagePrompt.message_lines=mirror_strs
        bpy.ops.elfin.message_prompt('INVOKE_DEFAULT',
            title='List Mirror Result',
            icon='INFO')
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return get_selection_len() == 1 and  \
            get_selected().elfin.is_module()

class UnlinkMirrors(bpy.types.Operator):
    bl_idname = 'elfin.unlink_mirrors'
    bl_label = 'Unlink mirrors from all selected modules.'
    bl_options = {'REGISTER', 'UNDO'}

    def unlink_mirrors(self, mirrors, recursive):
        if recursive:
            for o in get_selected(-1):
                for m in o.elfin.mirrors:
                    if m != o: m.elfin.mirrors = []
                o.elfin.mirrors = []
        else:
            for o in get_selected(-1):
                o.elfin.mirrors = []

        MessagePrompt.message_lines=['Operation successful']
        bpy.ops.elfin.message_prompt('INVOKE_DEFAULT',
            title='Unlink Mirrors',
            icon='INFO')

    def execute(self, context):
        mirrors = get_selected(-1) 
        YesNoPrmopt.callback_true = \
            YesNoPrmopt.Callback(self.unlink_mirrors, [mirrors, True])
        YesNoPrmopt.callback_false = \
            YesNoPrmopt.Callback(self.unlink_mirrors, [mirrors, False])
        bpy.ops.elfin.yes_no_prompt('INVOKE_DEFAULT',
            option=True,
            title='Unlink recursively?',
            message='Yes')

        return {'FINISHED'}

    @classmethod
    def poll(self, context):
        return get_selection_len() > 0

class LinkByMirror(bpy.types.Operator):
    bl_idname = 'elfin.link_by_mirror'
    bl_label = 'Link multiple modules of the same prototype by mirror'
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def can_link(cls):
        """Only show operator if selected objects are of the same prototype
        """
        selection = get_selected(-1)
        if selection:
            mod_name = selection[0].elfin.module_name
            for o in selection:
                if not o.elfin.is_module() or o.elfin.module_name != mod_name:
                    return False
            return True

    def link_by_mirror(self, mirrors):
        for m in mirrors:
            m.elfin.mirrors = mirrors
        MessagePrompt.message_lines=['Operation successful']
        bpy.ops.elfin.message_prompt('INVOKE_DEFAULT',
            title='Link by Mirror',
            icon='INFO')

    def execute(self, context):
        if not LinkByMirror.can_link():
            self.report(
                {'ERROR'}, 
                ('Selection is not homogenous i.e. some selected modules '
                    ' have a different prototype'))
            return {'CANCELLED'}

        mirrors = get_selected(-1)

        # Check for existing mirrors and warn user about it
        existing = False
        for m in mirrors:
            if m.elfin.mirrors:
                existing = True
                break

        if existing:
            YesNoPrmopt.callback_true = \
                YesNoPrmopt.Callback(self.link_by_mirror, [mirrors])
            bpy.ops.elfin.yes_no_prompt('INVOKE_DEFAULT',
                option=False,
                title='{} already has mirrors. Replace?'.format(m.name),
                message='Yes, replace.')
        else:
            self.link_by_mirror(mirrors)

        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return cls.can_link()

class JoinNetworks(bpy.types.Operator):
    bl_idname = 'elfin.join_networks'
    bl_label = 'Join two compatible networks'
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        raise NotImplementedError

class ExtrudeModule(bpy.types.Operator):
    bl_idname = 'elfin.extrude_module'
    bl_label = 'Extrude module'
    bl_property = "terminus_selector"
    bl_options = {'REGISTER'}

    def get_available_termini(self, context):
        available_termini = []

        # Save state into singleton
        LS = LivebuildState()
        LS.update_extrudables()

        if len(LS.n_extrudables) > 0:
            available_termini.append(('N', 'N', ''))
        if len(LS.c_extrudables) > 0:
            available_termini.append(('C', 'C', ''))

        return available_termini if len(available_termini) > 0 else [('-NA-', '-NA-', '')]

    terminus_selector = bpy.props.EnumProperty(items=get_available_termini)

    def execute(self, context):
        if self.terminus_selector.lower() == 'n':
            return bpy.ops.elfin.extrude_nterm(
                'INVOKE_DEFAULT')
        elif self.terminus_selector.lower() == 'c':
            return bpy.ops.elfin.extrude_cterm(
                'INVOKE_DEFAULT')
        else:
            raise ValueError('Unknown terminus selector')
            return {'CANCELLED'}

    def invoke(self, context, event):
        self.color = ColorWheel().next_color()
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return suitable_for_extrusion(context)

class ExtrudeNTerm(bpy.types.Operator):
    bl_idname = 'elfin.extrude_nterm'
    bl_label = 'Extrude N (add a module to the nterm)'
    bl_property = "nterm_ext_module_selector"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nterm_ext_module_selector = bpy.props.EnumProperty(
        items=lambda self, context: LivebuildState().n_extrudables)
    color = bpy.props.FloatVectorProperty(name="Display Color", 
                                        subtype='COLOR', 
                                        default=[0,0,0])

    def execute(self, context):
        execute_extrusion(
            which_term='n',
            selector=self.nterm_ext_module_selector, 
            color=self.color)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.color = ColorWheel().next_color()
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return suitable_for_extrusion(context)

class ExtrudeCTerm(bpy.types.Operator):
    bl_idname = 'elfin.extrude_cterm'
    bl_label = 'Extrude C (add a module to the cterm)'
    bl_property = "cterm_ext_module_selector"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def get_prototype_list(self, context):
        return get_extrusion_prototype_list('c')

    cterm_ext_module_selector = bpy.props.EnumProperty(
        items=lambda self, context: LivebuildState().c_extrudables)
    color = bpy.props.FloatVectorProperty(name="Display Color", 
                                        subtype='COLOR', 
                                        default=[0,0,0])

    def execute(self, context):
        execute_extrusion(
            which_term='c',
            selector=self.cterm_ext_module_selector, 
            color=self.color)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.color = ColorWheel().next_color()
        context.window_manager.invoke_search_popup(self)
        return {'FINISHED'}

    @classmethod
    def poll(cls, context):
        return suitable_for_extrusion(context)

class LoadXdb(bpy.types.Operator):
    bl_idname = 'elfin.load_xdb'
    bl_label = '(Re)load xdb'

    def execute(self, context):
        LivebuildState().load_xdb()
        return {'FINISHED'}

class LoadModuleLibrary(bpy.types.Operator):
    bl_idname = 'elfin.load_module_library'
    bl_label = '(Re)load module library'

    def execute(self, context):
        LivebuildState().load_library()
        return {'FINISHED'}

class MessagePrompt(bpy.types.Operator):
    """Elfin Module Collision Message"""
    bl_idname = 'elfin.message_prompt'
    bl_label = 'Prompts a message with an OK button'
    bl_options = {'REGISTER', 'INTERNAL'}

    title = bpy.props.StringProperty(default='Elfin Message')
    icon = bpy.props.StringProperty(default='ERROR')
    message_lines = []

    def execute(self, context):
        # Manually reset values
        self.message_lines = []
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_popup(self)
 
    def draw(self, context):
        self.layout.label(self.title, icon=self.icon)
        row = self.layout.column()
        for l in self.message_lines:
            row.label(l)

# Credits to
# https://blender.stackexchange.com/questions/73286/how-to-call-a-confirmation-dialog-box
class YesNoPrmopt(bpy.types.Operator):
    bl_idname = 'elfin.yes_no_prompt'
    bl_label = 'Confirm option'
    bl_options = {'REGISTER', 'INTERNAL'}
    
    title = bpy.props.StringProperty(default='Confirm?')
    icon = bpy.props.StringProperty(default='QUESTION')

    message = bpy.props.StringProperty(default='No')
    option = bpy.props.BoolProperty(default=True)

    class Callback:
        def __init__(self, func=None, args=[], kwargs=[]):
            self.func = func
            self.args = args
            self.kwargs = kwargs

    callback_true = Callback()
    callback_false = Callback()

    def execute(self, context):
        if self.option and self.callback_true.func:
            self.callback_true.func(
                *self.callback_true.args, 
                *self.callback_true.kwargs)
        elif self.callback_false.func:
            self.callback_false.func(
                *self.callback_false.args, 
                *self.callback_false.kwargs)

        # Manually reset values
        self.callback_true = self.Callback()
        self.callback_false = self.Callback()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        row.label(self.title, icon=self.icon)
        row.prop(self, 'option', text=self.message)

class CheckCollisionAndDelete(bpy.types.Operator):
    bl_idname = 'elfin.check_collision_and_delete'
    bl_label = 'Check collision and delete if positive'

    # Allow keyword specification
    object_name = bpy.props.StringProperty(default='__unset__')

    def execute(self, context):
        found_overlap = False

        try:
            ob = bpy.data.objects[self.object_name]
            found_overlap |= delete_if_overlap(ob)
        except KeyError:
            # No valid object_name specified - use selection
            for ob in get_selected(-1):
                if ob.elfin.is_module():
                    found_overlap |= delete_if_overlap(ob)
                else:
                    print('No overlap: {}'.format(ob.name))

        if found_overlap:
            MessagePrompt.message_lines=['Collision was detected and modules were deleted.']
            bpy.ops.elfin.message_prompt('INVOKE_DEFAULT')
        return {'FINISHED'}

    def invoke(self, context, event):
        self.object_name = ''

class PlaceModule(bpy.types.Operator):
    bl_idname = 'elfin.place_module'
    bl_label = 'Place a module'
    bl_property = 'module_to_place'
    bl_options = {'REGISTER', 'UNDO'}

    ask_prototype = bpy.props.BoolProperty(default=True, options={'HIDDEN'})
    module_to_place = bpy.props.EnumProperty(items=LivebuildState().placeables)
    color = bpy.props.FloatVectorProperty(name="Display Color", 
                                        subtype='COLOR', 
                                        default=[0,0,0])

    def execute(self, context):
        print('Execute: ', self.module_to_place)
        if self.module_to_place in nop_enum_tuples:
            return {'FINISHED'}

        print('Placing module {}'.format(self.module_to_place))
        
        sel_mod_name = self.module_to_place.split('.')[1]
        lmod = link_module(sel_mod_name)

        give_module_new_color(lmod, self.color)
        lmod.hide = False # By default the obj is hidden
        lmod.select = True

        self.ask_prototype = True
        return {'FINISHED'}

    def invoke(self, context, event):
        self.color = ColorWheel().next_color()

        if self.ask_prototype:
            context.window_manager.invoke_search_popup(self)
        else:
            return self.execute(context)

        return {'FINISHED'}

class INFO_MT_mesh_elfin_add(bpy.types.Menu):
    bl_idname = 'INFO_MT_elfin_add'
    bl_label = 'elfin'
    def draw(self, context):
        layout = self.layout

        for mod_tuple in LivebuildState().placeables:
            if mod_tuple in nop_enum_tuples:
                continue
            mod_name = mod_tuple[0]
            props = layout.operator('elfin.place_module', text=mod_name)
            props.module_to_place = mod_name
            props.ask_prototype = False