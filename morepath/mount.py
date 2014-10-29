from . import generic
from .path import register_path
from .request import Request


def register_mount(base_app, app, path, get_variables, converters, required,
                   get_converters, mount_name, app_factory):
    register_path(base_app, app, path, get_variables,
                  converters, required, get_converters, False,
                  app_factory)

    base_app.mounted[app] = app  # XXX turn into a set
    mount_name = mount_name or path
    base_app.named_mounted[mount_name] = app


def register_defer_links(base_app, app, model, context_factory):
    def get_link(request, obj, mounted):
        child = request.app.child(app, **context_factory(obj))
        return generic.link(request, obj, child, lookup=child.lookup)
    base_app.register(generic.link, [Request, model, object], get_link)
