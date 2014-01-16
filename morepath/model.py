from morepath import generic
from morepath.traject import Traject, ParameterFactory, Path
from morepath.publish import publish

from reg import mapply, arginfo

class Mount(object):
    def __init__(self, app, context_factory, variables):
        self.app = app
        self.context_factory = context_factory
        self.variables = variables

    def create_context(self):
        return mapply(self.context_factory, **self.variables)

    def __repr__(self):
        try:
            name = self.app.name
        except AttributeError:
            name = repr(self.app)
        return '<morepath.Mount of app %r with variables %r>' % (
            name, self.variables)

    def lookup(self):
        return self.app.lookup()

    def __call__(self, environ, start_response):
        request = self.app.request(environ)
        response = publish(request, self)
        return response(environ, start_response)

    def parent(self):
        return self.variables.get('base')

    def child(self, app, **context):
        factory = self.app._mounted.get(app)
        if factory is None:
            return None
        if 'base' not in context:
            context['base'] = self
        return factory(**context)


def get_arguments(callable, exclude):
    """Get dictionary with arguments and their default value.

    If no default is given, default value is taken to be None.
    """
    info = arginfo(callable)
    result = {}
    defaults = info.defaults or []
    defaults = [None] * (len(info.args) - len(defaults)) + list(defaults)
    return { name: default for (name, default) in zip(info.args, defaults)
             if name not in exclude }


def get_converters(arguments, converters, converter_for_value):
    """Get converters for arguments.

    Use explicitly supplied converter if available, otherwise ask
    app for converter for the default value of argument.
    """
    result = {}
    for name, value in arguments.items():
        converter = converters.get(name, None)
        if converter is not None:
            result[name] = converter
            continue
        result[name] = converter_for_value(value)
    return result


def get_url_parameters(arguments, exclude):
    return { name: default for (name, default) in arguments.items() if
             name not in exclude }


def get_variables_func(arguments, exclude):
    names = [name for name in arguments.keys() if name not in exclude]
    return lambda model: { name: getattr(model, name) for
                           name in names}


def register_root(app, model, variables, converters, model_factory):
    register_model(app, model, '', variables, converters, model_factory)


def register_model(app, model, path, variables, converters,
                   model_factory, base=None, get_base=None, arguments=None):
    if base is not None:
        traject = app.exact(generic.traject, [base])
        if traject is None:
            traject = Traject()
            app.register(generic.traject, [base], lambda base: traject)
    else:
        traject = app.traject
        if traject is None:
            traject = Traject()
            app.traject = traject

    converters = converters or {}
    if arguments is None:
        arguments = get_arguments(model_factory, ['request', 'base'])
    converters = get_converters(arguments, converters, app.converter_for_value)
    exclude = Path(path).variables()
    exclude.update(app.mount_variables())
    parameters = get_url_parameters(arguments, exclude)
    required = []
    parameter_factory = ParameterFactory(parameters, converters, required)

    if variables is None:
        variables = get_variables_func(arguments, app.mount_variables())

    traject.add_pattern(path, (model_factory, parameter_factory),
                        converters)
    traject.inverse(model, path, variables, converters, list(parameters.keys()))

    if get_base is None:
        def get_base(model):
            return app

    app.register(generic.base, [model], get_base)


def register_mount(base_app, app, path, context_factory):
    # specific class as we want a different one for each mount
    class SpecificMount(Mount):
        def __init__(self, **kw):
            super(SpecificMount, self).__init__(app, context_factory, kw)
    # need to construct argument info from context_factory, not SpecificMount
    arguments = get_arguments(context_factory, ['request', 'base'])
    register_model(base_app, SpecificMount, path, lambda m: m.variables,
                   None, SpecificMount, arguments=arguments)
    register_mounted(base_app, app, SpecificMount)


def register_mounted(base_app, app, model_factory):
    base_app._mounted[app] = model_factory
