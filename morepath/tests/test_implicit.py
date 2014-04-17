import morepath
import reg
from webtest import TestApp as Client


def setup_module(module):
    morepath.enable_implicit()


def setup_function(f):
    reg.implicit.clear()


def test_implicit_function():
    config = morepath.setup()
    app = morepath.App(testing_config=config)

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @reg.generic
    def one():
        return "Default one"

    @reg.generic
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

    config.commit()

    c = Client(app)

    response = c.get('/')
    assert response.body == b'The real two'


def test_implicit_function_mounted():
    config = morepath.setup()
    alpha = morepath.App(testing_config=config)
    beta = morepath.App(testing_config=config, variables=['id'])

    @alpha.mount(path='mounted/{id}', app=beta)
    def mount_beta(id):
        return {'id': id}

    class AlphaRoot(object):
        pass

    class Root(object):
        def __init__(self, id):
            self.id = id

    @alpha.path(path='/', model=AlphaRoot)
    def get_alpha_root():
        return AlphaRoot()

    @beta.path(path='/', model=Root)
    def get_root(id):
        return Root(id)

    @reg.generic
    def one():
        return "Default one"

    @reg.generic
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

    config.commit()

    c = Client(alpha)

    response = c.get('/mounted/1')
    assert response.body == b'View for 1, message: The real two'

    response = c.get('/')
    assert response.body == b'Default one'


def test_implicit_disabled():
    morepath.disable_implicit()
    config = morepath.setup()
    app = morepath.App(testing_config=config)

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @reg.generic
    def one():
        return "default one"

    @app.view(model=Model)
    def default(self, request):
        try:
            return one()
        except reg.NoImplicitLookupError:
            return "No implicit found"

    config.commit()

    c = Client(app)

    response = c.get('/')
    assert response.body == b'No implicit found'
