from morepath import generic
from morepath.traject import Traject, ParameterFactory, Path
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

    def parent(self):
        return self.variables.get('base')

    def child(self, app, **context):
        factory = self.app._mounted.get(app)
        if factory is None:
            return None
        if 'base' not in context:
            context['base'] = self
        return factory(**context)


def variables_from_arginfo(callable):
    """Construct variables function automatically from argument info.
    """
    info = arginfo(callable)
    args = set(info.args)
    args.discard('base')
    args.discard('request')
    return lambda model: { name: getattr(model, name) for
                           name in args }


def parameters_from_arginfo(path, callable):
    """Construct parameter information from arguments.

    Parameters are those function arguments that are not
    path variables.
    """
    info = arginfo(callable)
    result = {}
    defaults = info.defaults or []
    defaults = [None] * (len(info.args) - len(defaults)) + list(defaults)
    for name, default in zip(info.args, defaults):
        if name in ['request', 'base']:
            continue
        result[name] = default
    # Remove those parameters that belong to the path.
    path = Path(path)
    for name in path.variables():
        result.pop(name, None)
    return result


def register_root(app, model, variables, parameters, model_factory):
    register_model(app, model, '', variables, None, parameters, model_factory)


def register_model(app, model, path, variables, converters,
                   parameters, model_factory,
                   base=None, get_base=None):
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
    if converters is None:
        converters = {}
    if parameters is None:
        parameters = parameters_from_arginfo(path, model_factory)
    parameter_factory = ParameterFactory(parameters)
    traject.add_pattern(path, (model_factory, parameter_factory),
                        converters)
    if variables is None:
        variables = variables_from_arginfo(model_factory)
    traject.inverse(model, path, variables, converters, list(parameters.keys()))

    if get_base is None:
        def get_base(model):
            return app

    app.register(generic.base, [model], get_base)


def register_mount(base_app, app, path, parameters, context_factory):
    # specific class as we want a different one for each mount
    class SpecificMount(Mount):
        def __init__(self, **kw):
            super(SpecificMount, self).__init__(app, context_factory, kw)
    if parameters is None:
        parameters = parameters_from_arginfo(path, context_factory)
    register_model(base_app, SpecificMount, path, lambda m: m.variables,
                   None, parameters, SpecificMount)
    register_mounted(base_app, app, SpecificMount)


def register_mounted(base_app, app, model_factory):
    base_app._mounted[app] = model_factory
