import os
import json
import traceback

import bpy
import mathutils

from . import livebuild_helper as lh

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
    filepath = bpy.props.StringProperty(subtype="FILE_PATH")

    def invoke(self, context, event):
        self.filepath = os.path.splitext(bpy.data.filepath)[0] + '.json'
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        """Import elfin-solver JSON output into scene.
        """
        with open(self.filepath, 'r') as file:
            es_out = json.load(file)

        materialize(es_out)

        print('Input loaded from', self.filepath)

        return {'FINISHED'}

# Helpers ----------------------------------------
def materialize(es_out):
    # Reads elfin-solver output JSON and projects modules into the scene.

    for pgn_name in es_out:
        pg_network = es_out[pgn_name]

        # for solution in pg_network:
        print('------------------------------------------')
        print('---------------IMPORT LOGS----------------')
        print('------------------------------------------')

        if len(pg_network) == 0:
            print('ERROR: {} has no solutions!'
                .format(pgn_name))
            break

        print('Displaying best solution for {}'.format(pgn_name));
        solution = pg_network[0]

        first_node = True
        solution_nodes = []
        for node in solution['nodes']:
            print('Materialize: ', node['name'])

            if first_node:
                first_node = False

                # Add first module.
                new_mod = lh.add_module(
                    node['name'],
                    color=lh.ColorWheel().next_color())

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

        for node in solution_nodes:
            node.select = True