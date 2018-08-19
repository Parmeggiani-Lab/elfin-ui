import bpy

from . import livebuild_helper as LH

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
            target_nl = self.target_mod.elfin.n_linkage \
                if self.terminus == 'c' else \
                self.target_mod.elfin.c_linkage
            print('Severing: ', repr(self))

            # Remove back reference
            target_nl[self.target_chain_id].target_mod = None
            target_nl.remove(target_nl.find(self.target_chain_id))

        # Remove forward reference
        self.target_mod = None

class ObjectPointerWrapper(bpy.types.PropertyGroup):
    obj = bpy.props.PointerProperty(type=bpy.types.Object)

class ElfinObjectProperties(bpy.types.PropertyGroup):
    """Elfin's Object property catcher class"""
    obj_type = bpy.props.IntProperty(default=LH.ElfinObjType.NONE.value)
    module_name = bpy.props.StringProperty()
    module_type = bpy.props.StringProperty()
    obj_ptr = bpy.props.PointerProperty(type=bpy.types.Object)
    destroy_together = bpy.props.CollectionProperty(type=ObjectPointerWrapper)

    c_linkage = \
        bpy.props.CollectionProperty(type=Linkage)
    n_linkage = \
        bpy.props.CollectionProperty(type=Linkage)

    def is_module(self):
        return self.obj_type == LH.ElfinObjType.MODULE.value

    def is_joint(self):
        return self.obj_type == LH.ElfinObjType.PG_JOINT.value

    def is_bridge(self):
        return self.obj_type == LH.ElfinObjType.PG_BRIDGE.value

    def destroy(self):
        """Delete an object using default delete operator while preserving
        selection before deletion.
        """

        if self.is_module():
            self.cleanup_for_module()
        elif self.is_joint():
            for ch in self.obj_ptr.children:
                ch.elfin.destroy()
        elif self.is_bridge():
            ...
        else:
            print('elfin.destroy() called on non-elfin object:', self.obj_ptr.name)
            ...

        for opw in self.destroy_together:
            # if opw.obj.elfin.destroy_together
            # Remove back reference
            if opw.obj is None: continue
            dt = opw.obj.elfin.destroy_together
            i = 0
            while i < len(dt):
                if dt[i].obj == self.obj_ptr: dt.remove(i)
                else: i += 1

            opw.obj.elfin.destroy()

        LH.delete_object(self.obj_ptr)
        self.obj_ptr = None # Remove reference

    def cleanup_for_module(self):
        self.sever_links()

        # Destroy mirrors
        for m in self.mirrors:
            if m != self.obj_ptr:
                m.elfin.mirrors = []
                m.elfin.destroy()

        print('Module {} cleaned up.'.format(self.obj_ptr))

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
