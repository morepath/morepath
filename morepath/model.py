from .request import Request
from morepath import generic
from morepath.neotraject import Traject

def register_root(app, model, model_factory):

    def get_base(model):
        return app

    def root_path(request, model):
        return ''  # no path for root

    app.register(generic.path, [Request, model], root_path)
    app.register(generic.base, [model], get_base)
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
