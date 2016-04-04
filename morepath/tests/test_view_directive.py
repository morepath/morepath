import morepath
from morepath import generic
import dectate
from dectate import ConflictError
from webtest import TestApp as Client
from reg import ClassIndex, KeyIndex
import pytest
from morepath.core import request_method_predicate


def setup_module(module):
    morepath.disable_implicit()


def test_view_get_only():
    class App(morepath.App):
        pass

    @App.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @App.view(model=Model)
    def default(self, request):
        return "View"

    dectate.commit(App)

    c = Client(App())

    response = c.get('/')
    assert response.body == b'View'

    response = c.post('/', status=405)


def test_view_name_conflict_involving_default():
    class App(morepath.App):
        pass

    @App.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @App.view(model=Model)
    def default(self, request):
        return "View"

    @App.view(model=Model, name='')
    def default2(self, request):
        return "View"

    with pytest.raises(ConflictError):
        dectate.commit(App)


def test_view_custom_predicate_conflict_involving_default_extends():
    class Core(morepath.App):
        pass

    class App(Core):
        pass

    @Core.predicate(generic.view, name='extra', default='DEFAULT',
                    index=ClassIndex,
                    after=request_method_predicate)
    def dummy_predicate(request):
        return None

    @App.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @App.view(model=Model)
    def default(self, request):
        return "View"

    @App.view(model=Model, extra='DEFAULT')
    def default2(self, request):
        return "View"

    with pytest.raises(ConflictError):
        dectate.commit(Core, App)


def test_view_custom_predicate_without_fallback():
    class Core(morepath.App):
        pass

    class App(Core):
        pass

    @Core.predicate(generic.view, name='extra', default='DEFAULT',
                    index=KeyIndex,
                    after=request_method_predicate)
    def dummy_predicate(request):
        return 'match'

    @App.path(path='')
    class Model(object):
        def __init__(self):
            pass

    @App.view(model=Model, extra='match')
    def default(self, request):
        return "View"

    @App.view(model=Model, name='foo', extra='not match')
    def not_match(self, request):
        return "Not match"

    dectate.commit(Core, App)

    c = Client(App())

    response = c.get('/')
    assert response.body == b'View'
    c.get('/foo', status=404)
