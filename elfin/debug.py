
import bpy
import bpy.props
from . import elfin_properties

# Panels -----------------------------------------

class DebugPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Debug'
    bl_context = 'objectmode'
    bl_category = 'Elfin'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        col = row.column()
        col.operator('elfin.reset', text='Reset Properties')
        col.operator('elfin.load_module_library', text='(Re)load Library')
        col.operator('elfin.load_xdb', text='(Re)load xdb')
        col.operator('elfin.delete_faces', text='Delete faces (selection)')
        col.operator('elfin.load_all_obj_files', text='Load all obj files')
        col.operator('elfin.process_obj', text='Process obj file (selection)')
        col.operator('elfin.batch_process', text='Batch process all obj files')
        col.operator('elfin.place_module', text='Place a module into scene')
        col.operator('elfin.extrude_cterm', text='Extrude c-term')
        col.operator('elfin.extrude_nterm', text='Extrude n-term')
        col.prop(context.scene.elfin, 'disable_collision_check', text='Disable Collision Check')
