from . import generic
from .path import register_path


class MountRegistry(object):
    def __init__(self):
        self.clear()

    def clear(self):
        self.mounted = {}
        self.named_mounted = {}

    def register_mount(self, app, path, get_variables, converters, required,
                       get_converters, mount_name, app_factory):
        register_path(self, app, path, get_variables,
                      converters, required, get_converters, False,
                      app_factory)

        self.mounted[app] = app_factory
        mount_name = mount_name or path
        self.named_mounted[mount_name] = app_factory

    def register_defer_links(self, model, app_factory):
        self.register(generic.deferred_link_app, [object, model],
                      app_factory)
