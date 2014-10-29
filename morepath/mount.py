from morepath import compat
from . import generic
from .path import register_path, get_arguments, SPECIAL_ARGUMENTS
from .reify import reify
from .request import Request
from reg import mapply
from .implicit import set_implicit


class Mount(object):
    def __init__(self, app, context, parent, variables):
        self.app = app
        self.context = context
        self.parent = parent
        self.variables = variables

    def __repr__(self):  # pragma: nocoverage
        context_info = ', '.join(["%s=%r" % t for t in
                                   sorted(self.context.items())])
        result = '<morepath.Mount of %s' % repr(self.app)
        if context_info:
            result += ' with context: %s>' % context_info
        else:
            result += '>'
        return result

    @reify
    def lookup(self):
        return self.app.registry.lookup

    def set_implicit(self):
        set_implicit(self.lookup)

    def __call__(self, environ, start_response):
        request = self.app.request(environ)
        request.mounted = self
        response = self.app.publish(request)
        return response(environ, start_response)

    def child(self, app, **variables):
        if isinstance(app, compat.string_types):
            factory = self.app.registry.named_mounted.get(app)
        else:
            factory = self.app.registry.mounted.get(app)
        if factory is None:
            return None
        return factory(parent=self, **variables)


def register_mount(base_app, app, path, converters, required, get_converters,
                   mount_name, context_factory):
    # specific class as we want a different one for each mount
    class SpecificMount(Mount):
        pass

    # a factory that can construct mount from variables
    def get_specific_mount(**variables):
        context = mapply(context_factory, **variables)
        if context is None:
            return None
        return SpecificMount(app, context, variables['parent'], variables)

    # need to construct argument info from context_factory, not SpecificMount
    arguments = get_arguments(context_factory, SPECIAL_ARGUMENTS)

    register_path(base_app, SpecificMount, path, lambda m: m.variables,
                  converters, required, get_converters, False,
                  get_specific_mount, arguments=arguments)

    base_app.mounted[app] = get_specific_mount
    mount_name = mount_name or path
    base_app.named_mounted[mount_name] = get_specific_mount


def register_defer_links(base_app, app, model, context_factory):
    def get_link(request, obj, mounted):
        factory = base_app.mounted.get(app)
        context = context_factory(obj)
        context['parent'] = mounted
        child = factory(**context)
        return generic.link(request, obj, child, lookup=child.lookup)
    base_app.register(generic.link, [Request, model, object], get_link)
