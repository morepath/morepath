import morepath
from morepath import generic
from morepath.error import ConflictError
from webtest import TestApp as Client
from reg import ClassIndex, KeyIndex
import pytest
from morepath.core import request_method_predicate


def setup_module(module):
    morepath.disable_implicit()


def setup_function(f):
    morepath.App.registry.clear()


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

    @core.predicate(generic.view, name='extra', default='DEFAULT',
                    index=ClassIndex,
                    after=request_method_predicate)
    def dummy_predicate(request):
        return None

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model)
    def default(self, request):
        return "View"

    @app.view(model=Model, extra='DEFAULT')
    def default2(self, request):
        return "View"

    with pytest.raises(ConflictError):
        config.commit()


def test_view_custom_predicate_without_fallback():
    config = morepath.setup()

    class core(morepath.App):
        testing_config = config

    class app(core):
        testing_config = config

    @core.predicate(generic.view, name='extra', default='DEFAULT',
                    index=KeyIndex,
                    after=request_method_predicate)
    def dummy_predicate(request):
        return 'match'

    @app.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @app.view(model=Model, extra='match')
    def default(self, request):
        return "View"

    @app.view(model=Model, name='foo', extra='not match')
    def not_match(self, request):
        return "Not match"

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'View'
    c.get('/foo', status=404)
