import os
import json
import traceback

import bpy

from . import livebuild_helper as helper

# Constants --------------------------------------
exporter_field = 'exporter'
elfin_ui_exporter = 'elfin-ui'

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
    bl_label = 'Export as Elfin input (#exp)'
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

        # Maybe limit export to selected pg_network in the future?
        networks, pg_networks = [], []
        for obj in context.scene.objects:
            if obj.elfin.is_network():
                networks.append(obj)
            elif obj.elfin.is_pg_network():
                pg_networks.append(obj)

        output = create_output(networks, pg_networks)

        valid, msg = validate_and_annotate(networks, pg_networks, output)

        if not valid:
            self.report({'ERROR'}, msg)
            return {'CANCELLED'}

        json.dump(output,
                  open(self.filepath, 'w'),
                  separators=(',', ':'),
                  ensure_ascii=False,
                  indent=4)

        blend_file_path = '_autosave.blend'.join(
            self.filepath.rsplit('.json', 1))
        bpy.ops.wm.save_mainfile(filepath=blend_file_path)

        return {'FINISHED'}

# Helpers ----------------------------------------


def coms_approximately_equal(a, b, tolerance=1e-5):
    return all(abs(x) < tolerance for x in a - b)


def produce(networks):
    return (c for nw in networks for c in nw.children)


def create_output(networks, pg_networks):
    """Blends module objects and path guide into an output dictionary.
    """

    # Empty networks won't be included
    output = {
        'exporter': 'elfin-ui',
        'version': '1.0',
        'networks': {nw.name: network_to_dict(nw)
                     for nw in networks if nw.children},
        'pg_networks': {nw.name: network_to_dict(nw)
                        for nw in pg_networks if nw.children}
    }

    return output


def validate_and_annotate(networks, pg_networks, output):
    """Checks through modules and joints for unintended collisions. Modifies
    output dictionary to mark occupancy.
    """
    validity, msg = True, ''

    """
    User errors to check:

    1. Module collisions

    2. Joints that collide with module:
        A) COM equal: assume the module is meant to replace the joint: "joint
           occupied by module". For any occupied joint, num of bridges must <=
           free termini in the ocucpant module. Otherwise error out as invalid
           occupancy.
        B) COM not equal: error out as unintentional collision.
        C) Joint collides with multiple modules.
    """
    try:
        collision_map = helper.get_module_collision_map()
        if any(collision_map.values()):
            # 1.
            validity = False
            colliding_pairs = set()
            for k, v in collision_map.items():
                for vmod in v:
                    if (vmod.name, k.name) in colliding_pairs:
                        continue
                    # Exclude reversed names
                    colliding_pairs.add((k.name, vmod.name))
            collision_info = \
                '\n'.join('\"{}\" collides with \"{}\"'.format(mod1, mod2)
                          for mod1, mod2 in colliding_pairs)
            msg = 'Collision detected!\n' + \
                    'Resolve the following collisions \n' + \
                    'before proceeding:\n' + \
                    collision_info
        else:
            # 2.
            for jt in produce(pg_networks):
                colliding_mods = helper.find_overlap(jt, produce(networks))
                if not colliding_mods:
                    continue
                print('{} collision: {}.'.format(jt.name, colliding_mods))
                if len(colliding_mods) == 1:
                    jt_com = jt.matrix_world.translation
                    mod = colliding_mods[0]
                    mod_com = mod.matrix_world.translation
                    if coms_approximately_equal(jt_com, mod_com):
                        # A)
                        if mod.elfin.get_available_links() < \
                                len(jt.elfin.pg_neighbors):
                            validity = False
                            msg = ('Module \"{}\" occupies '
                                   '(has the same COM as) '
                                   '\"{}\", but bridges exceed number of '
                                   'available termini in the module.').format(
                                mod.name, jt.name)
                            break
                        else:
                            annotate_hinge(output, jt, mod)
                    else:
                        # B)
                        validity = False
                        msg = ('Joint \"{}\" overlaps with module \"{}\", but '
                               'their COMs are not close enough to be '
                               'considered as an occupancy.\n'
                               'Try using #jtm or #mtj if an occupancy is '
                               'your intention.').format(jt.name, mod.name)
                        break
                else:
                    validity = False
                    msg = ('Joint \"{}\" overlaps with multiple modules.\n'
                           'Resolve its collision with the following before '
                           'proceeding:\n{}').\
                        format(jt.name,
                               '\n'.join(mod.name for mod in colliding_mods))
                    break

    except Exception as e:
        # If there's any other weird error, we don't want to proceed to
        # export.
        validity, msg = False, ''.join((str(e), '\n', traceback.format_exc()))

    return validity, msg


def network_to_dict(network):
    return {mod.name: mod.elfin.as_dict() for mod in network.children}


def annotate_hinge(output, jt, mod):
    """Writes information about a hinge (jt occupied by mod) into output.
    """
    # Mark occupancy
    output_jt = output['pg_networks'][jt.parent.name][jt.name]
    output_jt['occupant'] = mod.name
    output_jt['occupant_parent'] = mod.parent.name

    # Set translation tolerance for the immediate neighbor of the hinge joint
    for pgn in jt.elfin.pg_neighbors:
        bridge = pgn.obj
        for other_end_nb in bridge.elfin.pg_neighbors:
            other_end = other_end_nb.obj
            if other_end != jt:
                output_oe = \
                    output['pg_networks'][jt.parent.name][other_end.name]
                output_oe['hinge'] = jt.name
                output_oe['tx_tol'] = bridge.elfin.tx_tol
                break
