from .fixtures import (basic, nested, abbr, mapply_bug,
                       normalmethod, method, conflict, pkg, noconverter)
from morepath import setup
from morepath.error import (ConflictError, MountError, DirectiveError,
                            LinkError, DirectiveReportError)
from morepath.view import render_html
from morepath.converter import Converter
import morepath
import reg

import pytest
from webtest import TestApp as Client


def setup_module(module):
    morepath.disable_implicit()


def test_basic():
    config = setup()
    config.scan(basic)
    config.commit()

    c = Client(basic.app())

    response = c.get('/foo')

    assert response.body == b'The view for model: foo'

    response = c.get('/foo/link')
    assert response.body == b'/foo'


def test_basic_json():
    config = setup()
    config.scan(basic)
    config.commit()

    c = Client(basic.app())

    response = c.get('/foo/json')

    assert response.body == b'{"id": "foo"}'


def test_basic_root():
    config = setup()
    config.scan(basic)
    config.commit()

    c = Client(basic.app())

    response = c.get('/')

    assert response.body == b'The root: ROOT'

    # + is to make sure we get the view, not the sub-model as
    # the model is greedy
    response = c.get('/+link')
    assert response.body == b'/'


def test_nested():
    config = setup()
    config.scan(nested)
    config.commit()

    c = Client(nested.outer_app())

    response = c.get('/inner/foo')

    assert response.body == b'The view for model: foo'

    response = c.get('/inner/foo/link')
    assert response.body == b'/inner/foo'


def test_abbr():
    config = setup()
    config.scan(abbr)
    config.commit()

    c = Client(abbr.app())

    response = c.get('/foo')
    assert response.body == b'Default view: foo'

    response = c.get('/foo/edit')
    assert response.body == b'Edit view: foo'


def test_scanned_normal_method():
    config = setup()
    with pytest.raises(DirectiveError):
        config.scan(normalmethod)


def test_scanned_static_method():
    config = setup()
    config.scan(method)
    config.commit()

    c = Client(method.app())

    response = c.get('/static')
    assert response.body == b'Static Method'

    root = method.Root()
    assert isinstance(root.static_method(), method.StaticMethod)


def test_scanned_class_method():
    config = setup()
    config.scan(method)
    config.commit()

    c = Client(method.app())

    response = c.get('/class')
    assert response.body == b'Class Method'

    root = method.Root()
    assert isinstance(root.class_method(), method.ClassMethod)


def test_scanned_no_converter():
    config = setup()
    config.scan(noconverter)
    with pytest.raises(DirectiveReportError):
        config.commit()


def test_scanned_conflict():
    config = setup()
    config.scan(conflict)
    with pytest.raises(ConflictError):
        config.commit()


def test_scanned_some_error():
    config = setup()
    with pytest.raises(ZeroDivisionError):
        config.scan(pkg)


def test_scanned_caller_package():
    from .fixtures import callerpkg
    callerpkg.main()

    from .fixtures.callerpkg.other import app

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Hello world'


def test_scanned_caller_package_scan_module():
    from .fixtures import callerpkg2
    callerpkg2.main()

    from .fixtures.callerpkg2.other import app

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Hello world'


def test_scan_module_only_init():
    config = setup()
    from morepath.tests.fixtures import scanmodule
    from morepath.tests.fixtures.scanmodule import theapp
    config.scan(scanmodule, recursive=False)
    config.scan(theapp, recursive=False)
    config.commit()

    c = Client(scanmodule.app())

    response = c.get('/')

    assert response.body == b'The root: ROOT'

    c.get('/foo', status=404)


def test_scan_module_only_submodule():
    config = setup()
    from morepath.tests.fixtures.scanmodule import submodule, theapp
    from morepath.tests.fixtures import scanmodule
    config.scan(submodule, recursive=False)
    config.scan(theapp, recursive=False)
    config.commit()

    c = Client(scanmodule.app())

    c.get('/', status=404)

    response = c.get('/foo')

    assert response.body == b'The view for model: foo'


def test_imperative():
    class Foo(object):
        pass

    @reg.generic
    def target():
        pass

    class app(morepath.App):
        pass

    c = setup()
    foo = Foo()

    c.configurable(app.registry)
    c.action(app.function(target), foo)
    c.commit()

    assert target.component(lookup=app().lookup) is foo


def test_basic_imperative():
    class app(morepath.App):
        pass

    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_model(id):
        return Model(id)

    def default(self, request):
        return "The view for model: %s" % self.id

    def link(self, request):
        return request.link(self)

    def json(self, request):
        return {'id': self.id}

    def root_default(self, request):
        return "The root: %s" % self.value

    def root_link(self, request):
        return request.link(self)

    c = setup()
    c.configurable(app.registry)
    c.action(app.path(path=''), Root)
    c.action(app.path(model=Model, path='{id}'),
             get_model)
    c.action(app.view(model=Model),
             default)
    c.action(app.view(model=Model, name='link'),
             link)
    c.action(app.view(model=Model, name='json',
                      render=morepath.render_json),
             json)
    c.action(app.view(model=Root),
             root_default)
    c.action(app.view(model=Root, name='link'),
             root_link)
    c.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The view for model: foo'

    response = c.get('/foo/link')
    assert response.body == b'/foo'

    response = c.get('/foo/json')
    assert response.body == b'{"id": "foo"}'

    response = c.get('/')
    assert response.body == b'The root: ROOT'

    # + is to make sure we get the view, not the sub-model
    response = c.get('/+link')
    assert response.body == b'/'


def test_basic_testing_config():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='{id}')
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "The view for model: %s" % self.id

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    @app.view(model=Model, name='json', render=morepath.render_json)
    def json(self, request):
        return {'id': self.id}

    @app.view(model=Root)
    def root_default(self, request):
        return "The root: %s" % self.value

    @app.view(model=Root, name='link')
    def root_link(self, request):
        return request.link(self)

    config.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The view for model: foo'

    response = c.get('/foo/link')
    assert response.body == b'/foo'

    response = c.get('/foo/json')
    assert response.body == b'{"id": "foo"}'

    response = c.get('/')
    assert response.body == b'The root: ROOT'

    # + is to make sure we get the view, not the sub-model
    response = c.get('/+link')
    assert response.body == b'/'


def test_link_to_unknown_model():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Root)
    def root_link(self, request):
        try:
            return request.link(Model('foo'))
        except LinkError:
            return "Link error"

    @app.view(model=Root, name='default')
    def root_link_with_default(self, request):
        try:
            return request.link(Model('foo'), default='hey')
        except LinkError:
            return "Link Error"

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Link error'
    response = c.get('/default')
    assert response.body == b'Link Error'


def test_link_to_none():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Root)
    def root_link(self, request):
        return str(request.link(None) is None)

    @app.view(model=Root, name='default')
    def root_link_with_default(self, request):
        return request.link(None, default='unknown')

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'True'
    response = c.get('/default')
    assert response.body == b'unknown'


def test_link_with_parameters():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id, param):
            self.id = id
            self.param = param

    @app.path(model=Model, path='{id}')
    def get_model(id, param=0):
        assert isinstance(param, int)
        return Model(id, param)

    @app.view(model=Model)
    def default(self, request):
        return "The view for model: %s %s" % (self.id, self.param)

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    config.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The view for model: foo 0'

    response = c.get('/foo/link')
    assert response.body == b'/foo?param=0'

    response = c.get('/foo?param=1')
    assert response.body == b'The view for model: foo 1'

    response = c.get('/foo/link?param=1')
    assert response.body == b'/foo?param=1'


def test_root_link_with_parameters():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        def __init__(self, param=0):
            assert isinstance(param, int)
            self.param = param

    @app.view(model=Root)
    def default(self, request):
        return "The view for root: %s" % self.param

    @app.view(model=Root, name='link')
    def link(self, request):
        return request.link(self)

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'The view for root: 0'

    response = c.get('/link')
    assert response.body == b'/?param=0'

    response = c.get('/?param=1')
    assert response.body == b'The view for root: 1'

    response = c.get('/link?param=1')
    assert response.body == b'/?param=1'


def test_implicit_variables():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='{id}')
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "The view for model: %s" % self.id

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    config.commit()

    c = Client(app())

    response = c.get('/foo/link')
    assert response.body == b'/foo'


def test_implicit_parameters():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='foo')
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "The view for model: %s" % self.id

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    config.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The view for model: None'
    response = c.get('/foo?id=bar')
    assert response.body == b'The view for model: bar'
    response = c.get('/foo/link')
    assert response.body == b'/foo'
    response = c.get('/foo/link?id=bar')
    assert response.body == b'/foo?id=bar'


def test_implicit_parameters_default():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(model=Model, path='foo')
    def get_model(id='default'):
        return Model(id)

    @app.view(model=Model)
    def default(self, request):
        return "The view for model: %s" % self.id

    @app.view(model=Model, name='link')
    def link(self, request):
        return request.link(self)

    config.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The view for model: default'
    response = c.get('/foo?id=bar')
    assert response.body == b'The view for model: bar'
    response = c.get('/foo/link')
    assert response.body == b'/foo?id=default'
    response = c.get('/foo/link?id=bar')
    assert response.body == b'/foo?id=bar'


def test_simple_root():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class Hello(object):
        pass

    hello = Hello()

    @app.path(model=Hello, path='')
    def hello_model():
        return hello

    @app.view(model=Hello)
    def hello_view(self, request):
        return 'hello'

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'hello'


def test_json_directive():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.json(model=Model)
    def json(self, request):
        return {'id': self.id}

    config.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'{"id": "foo"}'


def test_redirect():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        def __init__(self):
            pass

    @app.view(model=Root, render=render_html)
    def default(self, request):
        return morepath.redirect('/')

    config.commit()

    c = Client(app())

    c.get('/', status=302)


def test_root_conflict():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    @app.path(path='')
    class Something(object):
        pass

    with pytest.raises(ConflictError):
        config.commit()


def test_root_conflict2():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    @app.path(path='/')
    class Something(object):
        pass

    with pytest.raises(ConflictError):
        config.commit()


def test_root_no_conflict_different_apps():
    config = setup()

    class app_a(morepath.App):
        testing_config = config

    class app_b(morepath.App):
        testing_config = config

    @app_a.path(path='')
    class Root(object):
        pass

    @app_b.path(path='')
    class Something(object):
        pass

    config.commit()


def test_model_conflict():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class A(object):
        pass

    @app.path(model=A, path='a')
    def get_a():
        return A()

    @app.path(model=A, path='a')
    def get_a_again():
        return A()

    with pytest.raises(ConflictError):
        config.commit()


def test_path_conflict():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class A(object):
        pass

    class B(object):
        pass

    @app.path(model=A, path='a')
    def get_a():
        return A()

    @app.path(model=B, path='a')
    def get_b():
        return B()

    with pytest.raises(ConflictError):
        config.commit()


def test_path_conflict_with_variable():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class A(object):
        pass

    class B(object):
        pass

    @app.path(model=A, path='a/{id}')
    def get_a(id):
        return A()

    @app.path(model=B, path='a/{id2}')
    def get_b(id):
        return B()

    with pytest.raises(ConflictError):
        config.commit()


def test_path_conflict_with_variable_different_converters():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class A(object):
        pass

    class B(object):
        pass

    @app.path(model=A, path='a/{id}', converters=Converter(decode=int))
    def get_a(id):
        return A()

    @app.path(model=B, path='a/{id}')
    def get_b(id):
        return B()

    with pytest.raises(ConflictError):
        config.commit()


def test_model_no_conflict_different_apps():
    config = setup()

    class app_a(morepath.App):
        testing_config = config

    class app_b(morepath.App):
        testing_config = config

    class A(object):
        pass

    @app_a.path(model=A, path='a')
    def get_a():
        return A()

    @app_b.path(model=A, path='a')
    def get_a_again():
        return A()

    config.commit()


def test_view_conflict():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class Model(object):
        pass

    @app.view(model=Model, name='a')
    def a_view(self, request):
        pass

    @app.view(model=Model, name='a')
    def a1_view(self, request):
        pass

    with pytest.raises(ConflictError):
        config.commit()


def test_view_no_conflict_different_names():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class Model(object):
        pass

    @app.view(model=Model, name='a')
    def a_view(self, request):
        pass

    @app.view(model=Model, name='b')
    def b_view(self, request):
        pass

    config.commit()


def test_view_no_conflict_different_predicates():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class Model(object):
        pass

    @app.view(model=Model, name='a', request_method='GET')
    def a_view(self, request):
        pass

    @app.view(model=Model, name='a', request_method='POST')
    def b_view(self, request):
        pass

    config.commit()


def test_view_no_conflict_different_apps():
    config = setup()

    class app_a(morepath.App):
        testing_config = config

    class app_b(morepath.App):
        testing_config = config

    class Model(object):
        pass

    @app_a.view(model=Model, name='a')
    def a_view(self, request):
        pass

    @app_b.view(model=Model, name='a')
    def a1_view(self, request):
        pass

    config.commit()


def test_view_conflict_with_json():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class Model(object):
        pass

    @app.view(model=Model, name='a')
    def a_view(self, request):
        pass

    @app.json(model=Model, name='a')
    def a1_view(self, request):
        pass

    with pytest.raises(ConflictError):
        config.commit()


def test_view_conflict_with_html():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class Model(object):
        pass

    @app.view(model=Model, name='a')
    def a_view(self, request):
        pass

    @app.html(model=Model, name='a')
    def a1_view(self, request):
        pass

    with pytest.raises(ConflictError):
        config.commit()


def test_function_conflict():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class A(object):
        pass

    def func(a):
        pass

    @app.function(func, A)
    def a_func(self, request):
        pass

    @app.function(func, A)
    def a1_func(self, request):
        pass

    with pytest.raises(ConflictError):
        config.commit()


def test_function_no_conflict_different_apps():
    config = setup()

    class app_a(morepath.App):
        testing_config = config

    class app_b(morepath.App):
        testing_config = config

    def func(a):
        pass

    class A(object):
        pass

    @app_a.function(func, A)
    def a_func(a):
        pass

    @app_b.function(func, A)
    def a1_func(a):
        pass

    config.commit()


def test_run_app_with_context_without_it():
    config = setup()

    class app(morepath.App):
        variables = ['mount_id']
        testing_config = config

    config.commit()

    with pytest.raises(MountError):
        app()


def test_mapply_bug():
    config = setup()
    config.scan(mapply_bug)
    config.commit()

    c = Client(mapply_bug.app())

    response = c.get('/')

    assert response.body == b'the root'


def test_abbr_imperative():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class Model(object):
        pass

    @app.path(path='/', model=Model)
    def get_model():
        return Model()

    with app.view(model=Model) as view:
        @view()
        def default(self, request):
            return "Default view"

        @view(name='edit')
        def edit(self, request):
            return "Edit view"

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Default view'

    response = c.get('/edit')
    assert response.body == b'Edit view'


def test_abbr_imperative_exception_propagated():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class Model(object):
        pass

    @app.path(path='/', model=Model)
    def get_model():
        return Model()

    with pytest.raises(ZeroDivisionError):
        with app.view(model=Model) as view:
            @view()
            def default(self, request):
                return "Default view"

            1/0
