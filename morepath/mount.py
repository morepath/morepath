from . import generic
from .path import register_path
from .request import Request


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

    def register_defer_links(self, app, model, context_factory):
        def get_link(request, obj, mounted):
            child = request.app.child(context_factory(obj))
            return generic.link(request, obj, child, lookup=child.lookup)

        self.register(generic.link, [Request, model, object], get_link)

        def get_view(request, obj):
            child = request.app.child(context_factory(obj))

            old_app = request.app
            child.set_implicit()
            request.app = child
            # Hack: use squirreled away _predicates from request
            view = generic.view.component(request, obj, lookup=child.lookup,
                                          default=None,
                                          predicates=request._predicates)
            if view is not None:
                result = view(request, obj)
            else:
                result = None
            old_app.set_implicit()
            request.app = old_app
            return result

        self.register(generic.view, [Request, model], get_view)

