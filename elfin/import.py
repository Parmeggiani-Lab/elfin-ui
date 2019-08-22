import os
import json
import traceback

import bpy
import mathutils

from . import livebuild_helper as lh
from .export import exporter_field, elfin_ui_exporter

# Operators --------------------------------------

class ImportPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Import'
    bl_context = 'objectmode'
    bl_category = 'Elfin'

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        col = row.column()
        col.operator('elfin.import', text='Import design')

# Operators --------------------------------------

class ImportOperator(bpy.types.Operator):
    bl_idname = 'elfin.import'
    bl_label = 'Import elfin-solver output (#imp)'
    bl_options = {'REGISTER', 'UNDO'}

    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        self.filepath = os.path.splitext(bpy.data.filepath)[0] + '.json'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        """Import elfin-solver or elfin-ui JSON output into scene.
        """
        with open(self.filepath, 'r') as file:
            json_data = json.load(file)

        err_msg = materialize(json_data)

        if len(err_msg) > 0:
            self.report({'ERROR'}, err_msg);
            return {'FINISHED'}
        else:
            return {'FINISHED'}

# Helpers ----------------------------------------
def materialize(json_data):
    # Reads elfin-solver or elfin-ui output JSON and projects modules into the
    # scene.

    err_msg = ""
    if json_data.get(exporter_field, '') == elfin_ui_exporter:
        raise Exception('Not Implemented Yet')
        for pgn_name in json_data['pg_networks']:
            print('TODO: Import PG network')

        networks = json_data['networks']
        for nw_name in networks:
            # nw = networks[nw_name]
            # for name in nw:
            #     nw[name]['name'] = name
            # nodes = (nw[name] for name in nw)
            # project_nodes(nodes, nw_name)
            print('TODO: Import network')
    else:
        for pgn_name in json_data:
            pg_network = json_data[pgn_name]

            # for solution in pg_network:
            print('------------------------------------------')
            print('---------------IMPORT LOGS----------------')
            print('------------------------------------------')

            if len(pg_network) == 0:
                err_msg += 'ERROR: {} has no decimated parts.\n'.format(pgn_name)
                continue

            for dec_name, dec_solutions in pg_network.items():

                print('Displaying best solution for {}:{}' \
                    .format(pgn_name, dec_name));
                if not dec_solutions:
                    err_msg += 'ERROR: {}:{} has no solutions.\n' \
                        .format(pgn_name, dec_name)
                    continue

                sol = dec_solutions[0]
                project_nodes(sol['nodes'], ':'.join([pgn_name, dec_name]))

    return err_msg

def project_nodes(nodes, new_nw_name):
    first_node = True
    solution_nodes = []
    for node in nodes:
        print('Projecting ', node['name'])

        if first_node:
            first_node = False

            # Add first module.
            new_mod = lh.add_module(
                node['name'],
                color=lh.ColorWheel().next_color(),
                follow_selection=False)

            solution_nodes.append(new_mod)

            # Project node.
            tx = mathutils.Matrix(node['rot']).to_4x4()
            tx.translation = [f/lh.blender_pymol_unit_conversion for f in node['tran']]
            new_mod.matrix_world = tx * new_mod.matrix_world

        else:
            src_term = prev_node['src_term'].lower()
            src_chain_name = prev_node['src_chain_name']
            dst_chain_name = prev_node['dst_chain_name']

            selector = lh.module_enum_tuple(
                node['name'], 
                extrude_from=src_chain_name, 
                extrude_into=dst_chain_name,
                direction=src_term)[0]

            imported, _ = lh.extrude_terminus(
                which_term=src_term,
                selector=selector,
                sel_mod=new_mod,
                color=lh.ColorWheel().next_color(),
                reporter=None)

            assert(len(imported) == 1)

            new_mod = imported[0]
            solution_nodes.append(new_mod)

        prev_node = node

    # Name network and select all nodes.
    if solution_nodes:
        solution_nodes[0].parent.name = new_nw_name

        for node in solution_nodes:
            node.select = True