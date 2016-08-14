import morepath
from webtest import TestApp as Client
from morepath.dispatch import delegate


def test_function_scope():
    class app(morepath.App):

        @delegate()
        def one(self):
            return "Default one"

        @delegate()
        def two(self):
            return "Default two"

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.function(app.one)
    def one_impl(app):
        return app.two()

    @app.function(app.two)
    def two_impl():
        return "The real two"

    @app.view(model=Model)
    def default(self, request):
        return request.app.one()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'The real two'


def test_function_scope_on_mounted_apps():
    class alpha(morepath.App):

        @delegate()
        def one(self):
            return "Default one"

        @delegate()
        def two(self):
            return "Default two"

    class beta(alpha):
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

    @beta.function(beta.one)
    def one_impl(app):
        return app.two()

    @beta.function(beta.two)
    def two_impl():
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
