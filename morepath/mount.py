from . import generic
from .path import register_path, get_arguments, SPECIAL_ARGUMENTS
from .request import Request
from reg import mapply


def register_mount(base_app, app, path, get_variables, converters, required,
                   get_converters, mount_name, context_factory):
    # a factory that can construct mount from variables
    def get_mounted(**variables):
        context = mapply(context_factory, **variables)
        if context is None:
            return None
        return app(variables['parent'], **context)

    # need to construct argument info from context_factory, not
    # get_mounted
    arguments = get_arguments(context_factory, SPECIAL_ARGUMENTS)

    if get_variables is None:
        def get_variables(app):
            return app.context

    register_path(base_app, app, path, get_variables,
                  converters, required, get_converters, False,
                  get_mounted, arguments=arguments)

    base_app.mounted[app] = app  # XXX turn into a set
    mount_name = mount_name or path
    base_app.named_mounted[mount_name] = app


def register_defer_links(base_app, app, model, context_factory):
    def get_link(request, obj, mounted):
        child = request.mounted.child(app, **context_factory(obj))
        return generic.link(request, obj, child, lookup=child.lookup)
    base_app.register(generic.link, [Request, model, object], get_link)
