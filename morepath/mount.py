# from . import generic
# from .path import register_path
# from .app import Registry


# class MountRegistry(object):
#     factory_arguments = {
#         'registry': Registry
#     }

#     def __init__(self, registry):
#         self.reg_registry = registry
#         self.mounted = {}
#         self.named_mounted = {}

#     def register_mount(self, app, converter_registry,
#                        path, get_variables, converters, required,
#                        get_converters, mount_name, app_factory):
#         register_path(self.reg_registry, converter_registry, app,
#                       path, get_variables,
#                       converters, required, get_converters, False,
#                       app_factory)

#         self.mounted[app] = app_factory
#         mount_name = mount_name or path
#         self.named_mounted[mount_name] = app_factory

#     def register_defer_links(self, model, app_factory):
#         self.reg_registry.register_function(
#             generic.deferred_link_app, app_factory,
#             obj=model)
