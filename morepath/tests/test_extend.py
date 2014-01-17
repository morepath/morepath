from morepath.app import App
from werkzeug.test import Client
from morepath import setup
from morepath.request import Response


def test_extends():
    config = setup()
    app = App(testing_config=config)
    extending = App(extends=[app], testing_config=config)

    @app.model(
        path='users/{username}',
        variables=lambda model: {'username': model.username})
    class User(object):
        def __init__(self, username):
            self.username = username

    @app.view(model=User)
    def render_user(request, model):
        return "User: %s" % model.username

    @extending.view(model=User, name='edit')
    def edit_user(request, model):
        return "Edit user: %s" % model.username

    config.commit()

    cl = Client(app, Response)
    response = cl.get('/users/foo')
    assert response.data == 'User: foo'
    response = cl.get('/users/foo/edit')
    assert response.status == '404 NOT FOUND'

    cl = Client(extending, Response)
    response = cl.get('/users/foo')
    assert response.data == 'User: foo'
    response = cl.get('/users/foo/edit')
    assert response.data == 'Edit user: foo'


def test_overrides_view():
    config = setup()
    app = App(testing_config=config)
    overriding = App(extends=[app], testing_config=config)

    @app.model(
        path='users/{username}',
        variables=lambda model: {'username': model.username})
    class User(object):
        def __init__(self, username):
            self.username = username

    @app.view(model=User)
    def render_user(request, model):
        return "User: %s" % model.username

    @overriding.view(model=User)
    def render_user2(request, model):
        return "USER: %s" % model.username

    config.commit()

    cl = Client(app, Response)
    response = cl.get('/users/foo')
    assert response.data == 'User: foo'

    cl = Client(overriding, Response)
    response = cl.get('/users/foo')
    assert response.data == 'USER: foo'


def test_overrides_model():
    app = App()
    overriding = App(extends=[app])

    c = setup()
    c.configurable(app)
    c.configurable(overriding)

    class User(object):
        def __init__(self, username):
            self.username = username

    c.action(
        app.model(
            path='users/{username}',
            variables=lambda model: {'username': model.username}),
        User)

    def render_user(request, model):
        return "User: %s" % model.username

    c.action(
        app.view(
            model=User),
        render_user)

    def get_user(username):
        if username != 'bar':
            return None
        return User(username)

    c.action(
        overriding.model(
            model=User,
            path='users/{username}',
            variables=lambda model: {'username': model.username}),
        get_user)

    c.commit()

    cl = Client(app, Response)
    response = cl.get('/users/foo')
    assert response.data == 'User: foo'
    response = cl.get('/users/bar')
    assert response.data == 'User: bar'

    cl = Client(overriding, Response)
    response = cl.get('/users/foo')
    assert response.status == '404 NOT FOUND'
    response = cl.get('/users/bar')
    assert response.data == 'User: bar'
