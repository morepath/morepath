import morepath
import reg
from webtest import TestApp as Client


def setup_module(module):
    morepath.disable_implicit()


def setup_function(f):
    reg.implicit.clear()


class ImplicitLookupRequest(morepath.Request):
    def visit_app(self, app):
        super(ImplicitLookupRequest, self).visit_app(app)
        reg.implicit.lookup = app.lookup


def test_implicit_function():
    class app(morepath.App):
        request_class = ImplicitLookupRequest

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @reg.dispatch()
    def one():
        return "Default one"

    @reg.dispatch()
    def two():
        return "Default two"

    @app.function(one)
    def one_impl():
        return two()

    @app.function(two)
    def two_impl():
        return "The real two"

    @app.view(model=Model)
    def default(self, request):
        return one()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'The real two'


def test_implicit_function_mounted():
    class alpha(morepath.App):
        request_class = ImplicitLookupRequest

    class beta(morepath.App):
        def __init__(self, id):
            self.id = id

    @alpha.mount(path='mounted/{id}', app=beta)
    def mount_beta(id):
        return beta(id=id)

    class AlphaRoot(object):
        pass

    class Root(object):
        def __init__(self, id):
            self.id = id

    @alpha.path(path='/', model=AlphaRoot)
    def get_alpha_root():
        return AlphaRoot()

    @beta.path(path='/', model=Root)
    def get_root(app):
        return Root(app.id)

    @reg.dispatch()
    def one():
        return "Default one"

    @reg.dispatch()
    def two():
        return "Default two"

    @beta.function(one)
    def one_impl():
        return two()

    @beta.function(two)
    def two_impl():
        return "The real two"

    @alpha.view(model=AlphaRoot)
    def alpha_default(self, request):
        return one()

    @beta.view(model=Root)
    def default(self, request):
        return "View for %s, message: %s" % (self.id, one())

    c = Client(alpha())

    response = c.get('/mounted/1')
    assert response.body == b'View for 1, message: The real two'

    response = c.get('/')
    assert response.body == b'Default one'


def test_no_implicit_lookup():

    class app(morepath.App):
        pass

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @reg.dispatch()
    def one():
        return "default one"

    @app.view(model=Model)
    def default(self, request):
        try:
            return one()
        except reg.NoImplicitLookupError:
            return "No implicit found"

    c = Client(app())

    response = c.get('/')
    assert response.body == b'No implicit found'
