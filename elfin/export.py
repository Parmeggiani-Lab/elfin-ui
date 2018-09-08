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
        """Export to a JSON that specifies work areas for elfin-solver to
        solve. This format is not meant to fully specify the design in the
        current Blender file. The format is merely a work contract between
        elfin-ui and elfin-solver.
        
        """

        # Should we just export the selection?
        # For now let's do entire scene
        networks, pg_networks = [], []
        for obj in context.scene.objects:
            if obj.elfin.is_network():
                networks.append(obj)
            elif obj.elfin.is_pg_network():
                pg_networks.append(obj)
       
        """
        Format guide:
        {
            "networks": {
                "network": {
                    ...
                },
                "network.001": {
                    ...
                },
                "network.002": {
                    "D14.005": { // object name as key
                        "module_type": "single/hub/??",
                        "module_name": "D14",
                        "location": [...],
                        "rotation_euler": [...],
                        "n_linkage": [
                            {
                                "terminus": "n/c",
                                "source_chain_id": "A",
                                "target_mod_name": "D14.006", // converts to obj when parsed
                                "target_chain_id": "A"
                            }
                        ]
                        "c_linkage": [
                            ...
                        ]
                    },
                    ...
                }
            },
            "pg_networks": {
                "pg_network": {
                    ...
                },
                "pg_network.001": {
                    "joint.007": {
                        "location": [...],
                        "rotation_euler": [...],
                        "joint_neighbours": [ // converts to bridges between joints
                            {
                                "joint.006",
                                "joint.008",
                                ...
                            }
                        ]
                    },
                    ...
                }
            }
        }
        
        # All modules in "networks" are ElfinObjType.MODULE
        """


        # Parse path guides
        
        # Save where?

        return {'FINISHED'}