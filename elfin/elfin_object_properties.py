import enum

import bpy
import mathutils
from . import livebuild_helper as lh

ElfinObjType = enum.Enum('ElfinObjType', 'NONE MODULE JOINT BRIDGE NETWORK PG_NETWORK')

class Linkage(bpy.types.PropertyGroup):
    terminus = bpy.props.StringProperty()
    source_chain_id = bpy.props.StringProperty()
    target_mod = bpy.props.PointerProperty(type=bpy.types.Object)
    target_chain_id = bpy.props.StringProperty()

    def __repr__(self):
        return 'Linkage => (Src CID={}, Tgt={}, Tgt CID={})'.format(
            self.source_chain_id, self.target_mod, self.target_chain_id)

    def sever(self):
        if self.target_mod:
            tl = self.target_mod.elfin.n_linkage \
                if self.terminus == 'c' else \
                self.target_mod.elfin.c_linkage
            print('Severing: ', repr(self))

            tl.remove(tl.find(self.target_chain_id))

class ObjectPointerWrapper(bpy.types.PropertyGroup):
    obj = bpy.props.PointerProperty(type=bpy.types.Object)

class ElfinObjectProperties(bpy.types.PropertyGroup):
    """Represents an elfin object (module/joint/bridge)."""
    obj_type = bpy.props.IntProperty(default=ElfinObjType.NONE.value)
    module_name = bpy.props.StringProperty()
    module_type = bpy.props.StringProperty()
    obj_ptr = bpy.props.PointerProperty(type=bpy.types.Object)

    c_linkage = bpy.props.CollectionProperty(type=Linkage)
    n_linkage = bpy.props.CollectionProperty(type=Linkage)
    pg_neighbours = bpy.props.CollectionProperty(type=ObjectPointerWrapper)

    def is_module(self):
        return self.obj_type == ElfinObjType.MODULE.value

    def is_joint(self):
        return self.obj_type == ElfinObjType.JOINT.value

    def is_bridge(self):
        return self.obj_type == ElfinObjType.BRIDGE.value

    def is_network(self):
        return self.obj_type == ElfinObjType.NETWORK.value

    def is_pg_network(self):
        return self.obj_type == ElfinObjType.PG_NETWORK.value

    def destroy(self):
        """Clean up elfin data of this object, then call delete on the
        associated object.
        """

        if self.is_module():
            self.cleanup_module()
        elif self.is_joint():
            self.cleanup_joint()
        elif self.is_bridge():
            self.cleanup_bridge()
        elif self.is_network() or self.is_pg_network():
            self.cleanup_network()
        else:
            return # No obj_ptr to delete

        print('Elfin object {} cleaned up.'.format(self.obj_ptr))

        # If this is the last object in the network, the network will be
        # deleted instead.
        if self.obj_ptr.parent and len(self.obj_ptr.parent.children) == 1:
            self.obj_ptr.parent.elfin.destroy()
        else:
            self.delete_object(self.obj_ptr)

    def delete_object(self, obj):
        """
        Delete the Blender object to which the current elfin object
        PropertyGroup is associated with, preserving selection. 
        """

        # Cache user selection
        selection = [o for o in bpy.context.selected_objects if o != obj]
        bpy.ops.object.select_all(action='DESELECT')

        # Delete using default operator
        obj.hide = False
        obj.select = True
        bpy.ops.object.delete(use_global=False)

        if obj and obj.name in bpy.data.objects:
            print('Object dirty exit:', obj.name)
            # Remove it from bpy.data.objects because sometimes leftover
            # refereneces can cause the object to remain.
            bpy.data.objects.remove(obj)

        # Restore selection
        for ob in selection:
            if ob: ob.select = True

    def cleanup_network(self):
        """Delete all children modules."""
        # [!] Do not call destroy on children modules. It will cause infinite
        # call loop.
        for obj in self.obj_ptr.children:
            self.delete_object(obj)

    def cleanup_bridge(self):
        """Remove references of self object and also pointer to joints."""
        for opw in self.pg_neighbours:
            if opw.obj:
                rem_idx = -1
                jnb = opw.obj.elfin.pg_neighbours
                for i in range(len(jnb)):
                    if jnb[i].obj == self.obj_ptr:
                        rem_idx = i
                        break
                if rem_idx != -1:
                    jnb.remove(rem_idx)

    def cleanup_joint(self):
        """Delete connected bridges"""
        while len(self.pg_neighbours) > 0:
            self.pg_neighbours[0].obj.elfin.destroy()

    def cleanup_module(self):
        # Preserve neighbour nodes
        neighbours = {}
        for lk in self.c_linkage:
            if lk.target_mod:
                neighbours[lk.target_mod.name] = lk.target_mod
        for lk in self.n_linkage:
            if lk.target_mod:
                neighbours[lk.target_mod.name] = lk.target_mod
        old_network = self.obj_ptr.parent
        self.sever_links()

        # Destroy mirrors
        for m in self.mirrors:
            if m and m != self.obj_ptr:
                m.elfin.mirrors = []
                m.elfin.destroy()

        # Separate networks
        while neighbours:
            name, nb = neighbours.popitem()

            # Could become None is some weird situations, such as a deleted mirrors, etc.
            if nb and nb.parent == old_network:
                lh.move_to_new_network(nb)
                print('Moved',nb)


    def init_network(self, obj, network_type):
        assert network_type in {'module', 'pguide'}
        is_module_network = network_type == 'module'

        self.obj_ptr = obj
        self.obj_type = \
            ElfinObjType.NETWORK.value \
            if is_module_network else \
            ElfinObjType.PG_NETWORK.value
        obj.name = 'network' if is_module_network else 'pg_network'

        # Want to shift focus to new module, not network
        obj.select = False

    def init_bridge(self, obj, joint_a, joint_b):
        self.obj_ptr = obj
        self.obj_type = ElfinObjType.BRIDGE.value

        # Cache locations
        jb_loc = mathutils.Vector(joint_b.location)

        # Move ja and jb to default locations
        joint_b.location = joint_a.location + mathutils.Vector([0, 5, 0])

        bridge = self.obj_ptr
        bridge.parent = joint_b

        bridge.constraints.new(type='COPY_LOCATION').target = joint_a
        bridge.constraints.new(type='COPY_ROTATION').target = joint_a

        stretch_cons = bridge.constraints.new(type='STRETCH_TO')
        stretch_cons.target = joint_b
        stretch_cons.bulge = 0.0

        bridge.elfin.pg_neighbours.add().obj = joint_a
        bridge.elfin.pg_neighbours.add().obj = joint_b
        joint_a.elfin.pg_neighbours.add().obj = bridge
        joint_b.elfin.pg_neighbours.add().obj = bridge

        # Restore joint_b location 
        # 
        # [!] Must call update so that constraints don't bug out. This works
        # normally in Blender console if you copy paste the code of this
        # function but will break in script if update() is not called.
        bpy.context.scene.update()
        joint_b.location = jb_loc

    def init_joint(self, obj):
        self.obj_ptr = obj
        self.obj_type = ElfinObjType.JOINT.value

    def init_module(self, obj, mod_name):
        self.obj_ptr = obj
        self.module_name = mod_name

        xdb = lh.LivebuildState().xdb
        single_xdata = xdb['single_data'].get(mod_name, None)
        if single_xdata:
            self.module_type = 'single'
        else:
            hub_xdata = xdb['hub_data'].get(mod_name, None)
            if hub_xdata:
                self.module_type = 'hub'
            else:
                print('Warning: user is trying to link a module that is neither single or hub type')
                single_a_name, single_b_name = mod_name.split('-')
                double_xdata = xdb['double_data'].get(
                    single_a_name, {}).get(
                    single_b_name, None)
                if double_xdata:
                    self.module_type = 'double'
                else:
                    raise ValueError('Module name not found in xdb: ', mod_name)
        self.obj_type = ElfinObjType.MODULE.value

        # Lock all transformation - only allow network parent to transform
        obj.lock_location = obj.lock_rotation = obj.lock_scale = [True, True, True]
        obj.lock_rotation_w = obj.lock_rotations_4d = True

        # Always trigger dirty exit so we can clean up
        obj.use_fake_user = True

    def new_c_link(self, source_chain_id, target_mod, target_chain_id):
        link = self.c_linkage.add()
        link.name = link.source_chain_id = source_chain_id
        link.terminus = 'c'
        link.target_mod = target_mod
        link.target_chain_id = target_chain_id

    def new_n_link(self, source_chain_id, target_mod, target_chain_id):
        link = self.n_linkage.add()
        link.name = link.source_chain_id = source_chain_id
        link.terminus = 'n'
        link.target_mod = target_mod
        link.target_chain_id = target_chain_id

    def show_links(self):
        print('Links of {}'.format(self.obj_ptr.name))
        print('C links:')
        for cl in self.c_linkage: print(repr(cl))
        print('N links:')
        for nl in self.n_linkage: print(repr(nl))

    def sever_links(self):
        for cl in self.c_linkage: cl.sever()
        for nl in self.n_linkage: nl.sever()

    @property
    def mirrors(self):
        return self.get('_mirrors', [])

    @mirrors.setter
    def mirrors(self, value):
        self['_mirrors'] = value
