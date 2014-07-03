import morepath
from morepath.error import ConflictError
from webtest import TestApp as Client
import pytest


def setup_module(module):
    morepath.disable_implicit()


def test_view_get_only():
    config = morepath.setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model)
    def default(self, request):
        return "View"
    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'View'

    response = c.post('/', status=405)


def test_view_any():
    config = morepath.setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model, request_method=morepath.ANY)
    def default(self, request):
        return "View"

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'View'

    response = c.post('/')
    assert response.body == b'View'


def test_view_name_conflict_involving_default():
    config = morepath.setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model)
    def default(self, request):
        return "View"

    @app.view(model=Model, name='')
    def default2(self, request):
        return "View"

    with pytest.raises(ConflictError):
        config.commit()


def test_view_custom_predicate_conflict_involving_default_extends():
    config = morepath.setup()

    class core(morepath.App):
        testing_config = config

    class app(core):
        testing_config = config

    @core.predicate(name='foo', order=100, default='DEFAULT')
    def get_foo(request, model):
        return 'foo'

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model)
    def default(self, request):
        return "View"

    @app.view(model=Model, foo='DEFAULT')
    def default2(self, request):
        return "View"

    with pytest.raises(ConflictError):
        config.commit()
