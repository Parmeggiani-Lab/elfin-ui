import time

import bpy

class ModuleLifetimeWatcher(object):
    """A watcher that periodically checks entrance and exit of Elfin modules
    """
    check_interval = 100 # ms
    def __init__(self):
        self.last_checked = 0
        self.prev_object_names = set()
        self.initialized = False

        # A non positive interval will cause update-call infinite loop and
        # crash Blender. Reason is that __call__ possibly causes another scene
        # update, which then calls __call__ again.
        assert self.check_interval > 0

    def __call__(self, scene):
        """Makes an instance callable by bpy.app.handlers

        This is an asynchornous method!!
        """

        # Need this following block because we can't get at Blender's data
        # when this handler is registered (which is when __init__() gets
        # called)
        if not self.initialized:
            self.prev_object_names = set(bpy.context.scene.objects.keys())
            self.initialized = True
            print('{} initialized'.format(__name__))
            return

        now = time.time() * 1000
        delta = now - self.last_checked
        if delta > self.check_interval:
            self.last_checked = now

            now_object_names = set(scene.objects.keys())
            
            # Even new modules might get immediately deleted due to collision.
            # However, the deletion at the collision detection operator takes
            # care of severing linkages and removing from bpy.data.objects.
            deleted_object_names = self.prev_object_names - now_object_names
            new_object_names = now_object_names - self.prev_object_names
            self.prev_object_names = now_object_names

            if deleted_object_names:
                print('All exiting objects: {}'.format(deleted_object_names))
            for don in deleted_object_names:
                self.on_module_exit(don)

            if new_object_names:
                print('All entering objects: {}'.format(new_object_names))
            for non in new_object_names:
                self.on_module_enter(non)

    def on_module_enter(self, object_name):
        """Entrance conditioned on absence of collision"""
        ob = bpy.data.objects[object_name]
        # New objects should never generate a KeyError, as opposed to
        # deleted objects.
        if ob.elfin.is_module:
            print('Module enter: {}'.format(ob))
            bpy.ops.elfin.check_collision_and_delete(object_name=ob.name)

    def on_module_exit(self, object_name):
        """Severe linkages"""
        try:
            ob = bpy.data.objects[object_name]
            # A dirty exit is when an object is deleted from the scene but
            # remains in bpy.data.objects due to some left over reference.
            # A KeyError would be generated if the object exited cleanly.
            if ob.elfin.is_module:
                print('Module dirty exit: {}'.format(ob))
                ob.elfin.sever_links()
                bpy.data.objects.remove(ob)
        except KeyError:
            pass
        except Exception as e:
            raise e