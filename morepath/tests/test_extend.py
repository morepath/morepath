from morepath.app import App
from morepath import setup
from webobtoolkit.client import Client
import morepath


def setup_module(module):
    morepath.disable_implicit()


def test_extends():
    config = setup()
    app = App(testing_config=config)
    extending = App(extends=[app], testing_config=config)

    @app.path(path='users/{username}')
    class User(object):
        def __init__(self, username):
            self.username = username

    @app.view(model=User)
    def render_user(self, request):
        return "User: %s" % self.username

    @extending.view(model=User, name='edit')
    def edit_user(self, request):
        return "Edit user: %s" % self.username

    config.commit()

    cl = Client(app)
    response = cl.get('/users/foo')
    assert response.body == 'User: foo'
    response = cl.get('/users/foo/edit')
    assert response.status == '404 Not Found'

    cl = Client(extending)
    response = cl.get('/users/foo')
    assert response.body == 'User: foo'
    response = cl.get('/users/foo/edit')
    assert response.body == 'Edit user: foo'


def test_overrides_view():
    config = setup()
    app = App(testing_config=config)
    overriding = App(extends=[app], testing_config=config)

    @app.path(path='users/{username}')
    class User(object):
        def __init__(self, username):
            self.username = username

    @app.view(model=User)
    def render_user(self, request):
        return "User: %s" % self.username

    @overriding.view(model=User)
    def render_user2(self, request):
        return "USER: %s" % self.username

    config.commit()

    cl = Client(app)
    response = cl.get('/users/foo')
    assert response.body == 'User: foo'

    cl = Client(overriding)
    response = cl.get('/users/foo')
    assert response.body == 'USER: foo'


def test_overrides_model():
    config = setup()
    app = App(testing_config=config)
    overriding = App(extends=[app], testing_config=config)

    @app.path(path='users/{username}')
    class User(object):
        def __init__(self, username):
            self.username = username

    @app.view(model=User)
    def render_user(self, request):
        return "User: %s" % self.username

    @overriding.path(model=User, path='users/{username}')
    def get_user(username):
        if username != 'bar':
            return None
        return User(username)

    config.commit()

    cl = Client(app)
    response = cl.get('/users/foo')
    assert response.body == 'User: foo'
    response = cl.get('/users/bar')
    assert response.body == 'User: bar'

    cl = Client(overriding)
    response = cl.get('/users/foo')
    assert response.status == '404 Not Found'
    response = cl.get('/users/bar')
    assert response.body == 'User: bar'
