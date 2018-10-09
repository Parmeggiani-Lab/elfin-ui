import os
import json

import bpy

from . import livebuild_helper as lh

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
    bl_label = 'Export as Elfin input (#xpel)'
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        self.filepath = os.path.splitext(bpy.data.filepath)[0] + '.json'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        """Export scene networks as a work contract between elfin-ui and
        elfin-solver. The output specifies work areas for elfin-solver to
        solve, and may or may not fully characterise the design in the current
        Blender file.
        """

        # Maybe we can limit export to seleced pg_network in the future.
        networks, pg_networks = [], []
        for obj in context.scene.objects:
            if obj.elfin.is_network():
                networks.append(obj)
            elif obj.elfin.is_pg_network():
                pg_networks.append(obj)

        output = create_output(networks, pg_networks)

        valid, msg = validate_pathguides(networks, pg_networks, output)
        if not valid:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        annotate_output(output)
        
        json.dump(output,
            open(self.filepath, 'w'),
            separators=(',', ':'),
            ensure_ascii=False,
            indent=4)

        return {'FINISHED'}

# Helpers ----------------------------------------

def coms_approximately_equal(com1, com2, tolerance=1e-5):
    return all(abs(x) < tolerance for x in a - b)

def validate_pathguides(networks, pg_networks, output):
    """Checks through modules and joints for unintended collisions. Modifies
    output dictionary to mark occupancy.
    """
    validity, msg = True, ''
       
    """
    User errors to check:
    
    1. Module collisions

    2. Joints that collide with module: 
        A) COM equal: assume the module is meant to replace the joint =>
           “occupied”. For each occupied joint, if the joint connects to
           more than one bridge then the occupant module shouldn’t be
           fully connected. If the module is fully connected, then elfin
           would not be able to build around it so there must be a
           mistake. Error out as invalid occupant joint.
        B) COM not equal: error out as unintentional collision.
    """
    try:
        if lh.overlapping_module_exists():
            validity = False
            msg = 'There are overlapping modules. Remove them first (try deleting colliding modules with #ccd).'
        else:
            for pg_nw in pg_networks:
                for jt in pg_nw.children:
                    jt_com = jt.matrix_world.translation

                    for nw in networks:
                        for mod in nw:

                            # if collide
                            if False:
                                mod_com = mod.matrix_world.translation
                                # A)
                                if coms_approximately_equal(jt_com, mod_com):
                                    ...
                                else:
                                    ...
                                # B)

    except Exception as e:
        validity, msg = False, str(e)

    return validity, msg

def create_output(networks, pg_networks):
    """Blends module objects and path guide into an output dictionary.
    """
    output = {
        'networks': {nw.name: network_to_dict(nw) for nw in networks}, 
        'pg_networks': {nw.name: network_to_dict(nw) for nw in pg_networks}
    }
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
    """

    return output

def network_to_dict(network):
    return {mod.name: mod.elfin.as_dict() for mod in network.children}

def annotate_output(output):
    """Analyses output content to see if we can make inference and limit
    module selection. Modifies output dictionary.
    """

    print('Not yet implemented')
    
    return output

