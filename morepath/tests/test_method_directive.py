import morepath
from webtest import TestApp as Client


def test_implicit_function():
    class app(morepath.App):
        @morepath.dispatch_method()
        def one(self):
            return "Default one"

        @morepath.dispatch_method()
        def two(self):
            return "Default two"

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.method(app.one)
    def one_impl(self):
        return self.two()

    @app.method(app.two)
    def two_impl(self):
        return "The real two"

    @app.view(model=Model)
    def default(self, request):
        return request.app.one()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'The real two'


def test_implicit_function_mounted():
    class base(morepath.App):
        @morepath.dispatch_method()
        def one(self):
            return "Default one"

        @morepath.dispatch_method()
        def two(self):
            return "Default two"

    class alpha(base):
        pass

    class beta(base):
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

    @beta.method(base.one)
    def one_impl(self):
        return self.two()

    @beta.method(base.two)
    def two_impl(self):
        return "The real two"

    @alpha.view(model=AlphaRoot)
    def alpha_default(self, request):
        return request.app.one()

    @beta.view(model=Root)
    def default(self, request):
        return "View for %s, message: %s" % (self.id, request.app.one())

    c = Client(alpha())

    response = c.get('/mounted/1')
    assert response.body == b'View for 1, message: The real two'

    response = c.get('/')
    assert response.body == b'Default one'
