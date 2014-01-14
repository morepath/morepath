from morepath import generic
from morepath.traject import Traject, ParameterFactory
from reg import mapply


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


def register_root(app, model, variables, parameters, model_factory):
    register_model(app, model, '', variables, parameters, model_factory)


def register_model(app, model, path, variables, parameters, model_factory,
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
    parameter_factory = ParameterFactory(parameters)
    traject.add_pattern(path, (model_factory, parameter_factory))
    if variables is None:
        variables = lambda m: {}
    traject.inverse(model, path, variables, list(parameters.keys()))

    if get_base is None:
        def get_base(model):
            return app

    app.register(generic.base, [model], get_base)


def register_mount(base_app, app, path, parameters, context_factory):
    # specific class as we want a different one for each mount
    class SpecificMount(Mount):
        def __init__(self, **kw):
            super(SpecificMount, self).__init__(app, context_factory, kw)
    register_model(base_app, SpecificMount, path, lambda m: m.variables,
                   parameters, SpecificMount)
    register_mounted(base_app, app, SpecificMount)


def register_mounted(base_app, app, model_factory):
    base_app._mounted[app] = model_factory
