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

    def register_defer_links(self, model, context_factory):
        def get_app(request, obj):
            context = context_factory(obj)
            if context is None:
                return request.app.parent
            return request.app.child(context)

        def get_link(request, obj, mounted):
            other = get_app(request, obj)
            if other is None:
                return None
            return generic.link(request, obj, other, lookup=other.lookup)

        self.register(generic.link, [Request, model, object], get_link)

        def get_view(request, obj):
            other = get_app(request, obj)
            if other is None:
                return None

            old_app = request.app
            other.set_implicit()
            request.app = other
            # Hack: use squirreled away _predicates from request
            view = generic.view.component(request, obj, lookup=other.lookup,
                                          default=None,
                                          predicates=request._predicates)
            if view is not None:
                result = view(request, obj)
            else:
                result = None
            old_app.set_implicit()
            request.app = old_app
            return result

        # these views are always internal so cannot be found
        get_view.internal = True

        self.register(generic.view, [Request, model], get_view)
