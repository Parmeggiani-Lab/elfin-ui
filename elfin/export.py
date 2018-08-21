import bpy


# Operators --------------------------------------

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
        """Export to a json that fully specifies network and path guide
        details.

        The addon should be able to read from this JSON and recreate and
        entire design.
        """

        # Should we just export the selection?
        # objs = bpy.data.object

        # Separate modules and pguides


        # Parse networks

        # Parse path guides
        
        # Save where?

        return {'FINISHED'}