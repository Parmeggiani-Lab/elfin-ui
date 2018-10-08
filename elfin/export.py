import os
import json

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
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        self.filepath = os.path.splitext(bpy.data.filepath)[0] + '.json'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        """Export to a JSON that specifies work areas for elfin-solver to
        solve. This format may or may not fully characterise the design in the
        current Blender file. The format is merely a work contract between
        elfin-ui and elfin-solver.        
        """
        output = {}

        # Maybe we can limit export to seleced pg_network in the future.
        networks, pg_networks = [], []
        for obj in context.scene.objects:
            if obj.elfin.is_network():
                networks.append(obj)
            elif obj.elfin.is_pg_network():
                pg_networks.append(obj)
       
        """
        User errors to check:
        
        Joints that collide with module: 
            A) COM equal: assume the module is meant to replace the joint =>
               “occupied”. For each occupied joint, if the joint connects to
               more than one bridge then the occupant module shouldn’t be
               fully connected. If the module is fully connected, then elfin
               would not be able to build around it so there must be a
               mistake. Error out as invalid occupant joint.
            B) COM not equal: error out as unintentional collision.
        """

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
        json.dump(output,
            open(self.filepath, 'w'),
            separators=(',', ':'),
            ensure_ascii=False,
            indent=4)

        return {'FINISHED'}
