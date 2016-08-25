import morepath
from webtest import TestApp as Client


def test_function_extends():
    class App(morepath.App):
        @morepath.dispatch_method('obj')
        def foo(self, obj):
            return "default"

    class Extending(App):
        pass

    class Alpha(object):
        pass

    @App.method(App.foo, obj=Alpha)
    def app_foo(app, obj):
        return "App"

    @Extending.method(App.foo, obj=Alpha)
    def extending_foo(app, obj):
        return "Extending"

    assert App().foo(Alpha()) == 'App'
    assert Extending().foo(Alpha()) == 'Extending'


def test_extends():
    class App(morepath.App):
        pass

    class Extending(App):
        pass

    @App.path(path='users/{username}')
    class User(object):
        def __init__(self, username):
            self.username = username

    @App.view(model=User)
    def render_user(self, request):
        return "User: %s" % self.username

    @Extending.view(model=User, name='edit')
    def edit_user(self, request):
        return "Edit user: %s" % self.username

    cl = Client(App())
    response = cl.get('/users/foo')
    assert response.body == b'User: foo'
    response = cl.get('/users/foo/edit', status=404)

    cl = Client(Extending())
    response = cl.get('/users/foo')
    assert response.body == b'User: foo'
    response = cl.get('/users/foo/edit')
    assert response.body == b'Edit user: foo'


def test_overrides_view():
    class App(morepath.App):
        pass

    class Overriding(App):
        pass

    @App.path(path='users/{username}')
    class User(object):
        def __init__(self, username):
            self.username = username

    @App.view(model=User)
    def render_user(self, request):
        return "User: %s" % self.username

    @Overriding.view(model=User)
    def render_user2(self, request):
        return "USER: %s" % self.username

    cl = Client(App())
    response = cl.get('/users/foo')
    assert response.body == b'User: foo'

    cl = Client(Overriding())
    response = cl.get('/users/foo')
    assert response.body == b'USER: foo'


def test_overrides_model():
    class App(morepath.App):
        pass

    class Overriding(App):
        pass

    @App.path(path='users/{username}')
    class User(object):
        def __init__(self, username):
            self.username = username

    @App.view(model=User)
    def render_user(self, request):
        return "User: %s" % self.username

    @Overriding.path(model=User, path='users/{username}')
    def get_user(username):
        if username != 'bar':
            return None
        return User(username)

    cl = Client(App())
    response = cl.get('/users/foo')
    assert response.body == b'User: foo'
    response = cl.get('/users/bar')
    assert response.body == b'User: bar'

    cl = Client(Overriding())
    response = cl.get('/users/foo', status=404)
    response = cl.get('/users/bar')
    assert response.body == b'User: bar'
