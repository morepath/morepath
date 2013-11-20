from .request import Request
from morepath import generic
from morepath.traject import Traject
from reg import mapply

class Mount(object):
    def __init__(self, app, context_factory, variables):
        self.app = app
        self.context_factory = context_factory
        self.variables = variables

    def create_context(self):
        return mapply(self.context_factory, **self.variables)

    def __repr__(self):
        return '<morepath.Mount of app %r with variables %r>' % (
            self.app.name, self.variables)


def register_root(app, model, model_factory):
    register_model(app, model, '', lambda model: {}, model_factory)


def register_model(app, model, path, variables, model_factory,
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
    traject.add_pattern(path, model_factory)
    traject.inverse(model, path, variables)

    if get_base is None:
        def get_base(model):
            return app

    app.register(generic.base, [model], get_base)


def register_mount(app, mounted, path, context_factory):
    # specific class as we want a different one for each mount
    class SpecificMount(Mount):
        def __init__(self, **kw):
            super(SpecificMount, self).__init__(mounted, context_factory, kw)
    register_model(app, SpecificMount, path, lambda m: m.variables,
                   SpecificMount)
