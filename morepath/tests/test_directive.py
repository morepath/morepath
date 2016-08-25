import dectate
from .fixtures import (basic, nested, abbr, mapply_bug,
                       method, conflict, noconverter)
from dectate import ConflictError, DirectiveReportError
from morepath.error import LinkError
from morepath.view import render_html
from morepath.converter import Converter
import morepath
import reg

import pytest
from webtest import TestApp as Client


def test_basic():
    c = Client(basic.app())

    response = c.get('/foo')

    assert response.body == b'The view for model: foo'

    response = c.get('/foo/link')
    assert response.body == b'http://localhost/foo'


def test_basic_json():
    c = Client(basic.app())

    response = c.get('/foo/json')

    assert response.body == b'{"id": "foo"}'


def test_basic_root():
    c = Client(basic.app())

    response = c.get('/')

    assert response.body == b'The root: ROOT'

    # + is to make sure we get the view, not the sub-model as
    # the model is greedy
    response = c.get('/+link')
    assert response.body == b'http://localhost/'


def test_nested():
    c = Client(nested.outer_app())

    response = c.get('/inner/foo')

    assert response.body == b'The view for model: foo'

    response = c.get('/inner/foo/link')
    assert response.body == b'http://localhost/inner/foo'


def test_abbr():
    c = Client(abbr.app())

    response = c.get('/foo')
    assert response.body == b'Default view: foo'

    response = c.get('/foo/edit')
    assert response.body == b'Edit view: foo'


def test_scanned_static_method():
    c = Client(method.app())

    response = c.get('/static')
    assert response.body == b'Static Method'

    root = method.Root()
    assert isinstance(root.static_method(), method.StaticMethod)


def test_scanned_no_converter():
    with pytest.raises(DirectiveReportError):
        noconverter.app.commit()


def test_scanned_conflict():
    with pytest.raises(ConflictError):
        conflict.app.commit()


def test_basic_scenario():
    class app(morepath.App):
        pass

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

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The view for model: foo'

    response = c.get('/foo/link')
    assert response.body == b'http://localhost/foo'

    response = c.get('/foo/json')
    assert response.body == b'{"id": "foo"}'

    response = c.get('/')
    assert response.body == b'The root: ROOT'

    # + is to make sure we get the view, not the sub-model
    response = c.get('/+link')
    assert response.body == b'http://localhost/'


def test_link_to_unknown_model():
    class app(morepath.App):
        pass

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

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Link error'
    response = c.get('/default')
    assert response.body == b'Link Error'


def test_link_to_none():
    class app(morepath.App):
        pass

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

    c = Client(app())

    response = c.get('/')
    assert response.body == b'True'
    response = c.get('/default')
    assert response.body == b'unknown'


def test_link_with_parameters():
    class app(morepath.App):
        pass

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

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The view for model: foo 0'

    response = c.get('/foo/link')
    assert response.body == b'http://localhost/foo?param=0'

    response = c.get('/foo?param=1')
    assert response.body == b'The view for model: foo 1'

    response = c.get('/foo/link?param=1')
    assert response.body == b'http://localhost/foo?param=1'


def test_root_link_with_parameters():
    class app(morepath.App):
        pass

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

    c = Client(app())

    response = c.get('/')
    assert response.body == b'The view for root: 0'

    response = c.get('/link')
    assert response.body == b'http://localhost/?param=0'

    response = c.get('/?param=1')
    assert response.body == b'The view for root: 1'

    response = c.get('/link?param=1')
    assert response.body == b'http://localhost/?param=1'


def test_link_with_prefix():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root, name='link')
    def link(self, request):
        return request.link(self)

    @app.link_prefix()
    def link_prefix(request):
        return request.headers['TESTPREFIX']

    c = Client(app())

    # we don't do anything with the prefix, so a slash at the end of the prefix
    # leads to a double prefix at the end
    response = c.get('/link', headers={'TESTPREFIX': 'http://testhost/'})
    assert response.body == b'http://testhost//'

    response = c.get('/link', headers={'TESTPREFIX': 'http://testhost'})
    assert response.body == b'http://testhost/'


def test_link_with_prefix_app_arg():
    class App(morepath.App):
        pass

    @App.path(path='')
    class Root(object):
        pass

    @App.view(model=Root, name='link')
    def link(self, request):
        return request.link(self)

    @App.link_prefix()
    def link_prefix(app, request):
        assert isinstance(app, App)
        return request.headers['TESTPREFIX']

    c = Client(App())

    # we don't do anything with the prefix, so a slash at the end of the prefix
    # leads to a double prefix at the end
    response = c.get('/link', headers={'TESTPREFIX': 'http://testhost/'})
    assert response.body == b'http://testhost//'

    response = c.get('/link', headers={'TESTPREFIX': 'http://testhost'})
    assert response.body == b'http://testhost/'


def test_link_prefix_cache():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root, name='link')
    def link(self, request):
        request.link(self)  # make an extra call before returning
        return request.link(self)

    @app.link_prefix()
    def link_prefix(request):
        if not hasattr(request, 'callnumber'):
            request.callnumber = 1
        else:
            request.callnumber += 1
        return str(request.callnumber)

    c = Client(app())

    response = c.get('/link')
    assert response.body == b'1/'


def test_link_with_invalid_prefix():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root, name='link')
    def link(self, request):
        return request.link(self)

    @app.link_prefix()
    def link_prefix(request):
        return None

    c = Client(app())

    with pytest.raises(TypeError):
        c.get('/link')


def test_implicit_variables():
    class app(morepath.App):
        pass

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

    c = Client(app())

    response = c.get('/foo/link')
    assert response.body == b'http://localhost/foo'


def test_implicit_parameters():
    class app(morepath.App):
        pass

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

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The view for model: None'
    response = c.get('/foo?id=bar')
    assert response.body == b'The view for model: bar'
    response = c.get('/foo/link')
    assert response.body == b'http://localhost/foo'
    response = c.get('/foo/link?id=bar')
    assert response.body == b'http://localhost/foo?id=bar'


def test_implicit_parameters_default():
    class app(morepath.App):
        pass

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

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The view for model: default'
    response = c.get('/foo?id=bar')
    assert response.body == b'The view for model: bar'
    response = c.get('/foo/link')
    assert response.body == b'http://localhost/foo?id=default'
    response = c.get('/foo/link?id=bar')
    assert response.body == b'http://localhost/foo?id=bar'


def test_simple_root():
    class app(morepath.App):
        pass

    class Hello(object):
        pass

    hello = Hello()

    @app.path(model=Hello, path='')
    def hello_model():
        return hello

    @app.view(model=Hello)
    def hello_view(self, request):
        return 'hello'

    c = Client(app())

    response = c.get('/')
    assert response.body == b'hello'


def test_json_directive():
    class app(morepath.App):
        pass

    @app.path(path='{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.json(model=Model)
    def json(self, request):
        return {'id': self.id}

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'{"id": "foo"}'


def test_redirect():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        def __init__(self):
            pass

    @app.view(model=Root, render=render_html)
    def default(self, request):
        return morepath.redirect('/')

    c = Client(app())

    c.get('/', status=302)


def test_root_conflict():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.path(path='')
    class Something(object):
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_root_conflict2():
    class app(morepath.App):
        pass

    @app.path(path='')
    class Root(object):
        pass

    @app.path(path='/')
    class Something(object):
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_root_no_conflict_different_apps():
    class app_a(morepath.App):
        pass

    class app_b(morepath.App):
        pass

    @app_a.path(path='')
    class Root(object):
        pass

    @app_b.path(path='')
    class Something(object):
        pass

    dectate.commit(app_a, app_b)


def test_model_conflict():
    class app(morepath.App):
        pass

    class A(object):
        pass

    @app.path(model=A, path='a')
    def get_a():
        return A()

    @app.path(model=A, path='a')
    def get_a_again():
        return A()

    with pytest.raises(ConflictError):
        app.commit()


def test_path_conflict():
    class app(morepath.App):
        pass

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
        app.commit()


def test_path_conflict_with_variable():
    class app(morepath.App):
        pass

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
        app.commit()


def test_path_conflict_with_variable_different_converters():
    class app(morepath.App):
        pass

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
        app.commit()


def test_model_no_conflict_different_apps():
    class app_a(morepath.App):
        pass

    class app_b(morepath.App):
        pass

    class A(object):
        pass

    @app_a.path(model=A, path='a')
    def get_a():
        return A()

    @app_b.path(model=A, path='a')
    def get_a_again():
        return A()

    dectate.commit(app_a, app_b)


def test_view_conflict():
    class app(morepath.App):
        pass

    class Model(object):
        pass

    @app.view(model=Model, name='a')
    def a_view(self, request):
        pass

    @app.view(model=Model, name='a')
    def a1_view(self, request):
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_view_no_conflict_different_names():
    class app(morepath.App):
        pass

    class Model(object):
        pass

    @app.view(model=Model, name='a')
    def a_view(self, request):
        pass

    @app.view(model=Model, name='b')
    def b_view(self, request):
        pass

    app.commit()


def test_view_no_conflict_different_predicates():
    class app(morepath.App):
        pass

    class Model(object):
        pass

    @app.view(model=Model, name='a', request_method='GET')
    def a_view(self, request):
        pass

    @app.view(model=Model, name='a', request_method='POST')
    def b_view(self, request):
        pass

    app.commit()


def test_view_no_conflict_different_apps():
    class app_a(morepath.App):
        pass

    class app_b(morepath.App):
        pass

    class Model(object):
        pass

    @app_a.view(model=Model, name='a')
    def a_view(self, request):
        pass

    @app_b.view(model=Model, name='a')
    def a1_view(self, request):
        pass

    dectate.commit(app_a, app_b)


def test_view_conflict_with_json():
    class app(morepath.App):
        pass

    class Model(object):
        pass

    @app.view(model=Model, name='a')
    def a_view(self, request):
        pass

    @app.json(model=Model, name='a')
    def a1_view(self, request):
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_view_conflict_with_html():
    class app(morepath.App):
        pass

    class Model(object):
        pass

    @app.view(model=Model, name='a')
    def a_view(self, request):
        pass

    @app.html(model=Model, name='a')
    def a1_view(self, request):
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_function():
    class App(morepath.App):
        @morepath.dispatch_method('a')
        def func(self, a):
            return "default"

    class A(object):
        pass

    @App.method(App.func, a=A)
    def a_func(app, request):
        return "A"

    app = App()
    assert app.func(A()) == "A"
    assert app.func(None) == "default"


def test_method():
    class App(morepath.App):
        @morepath.dispatch_method('a')
        def func(self, a):
            return "default"

    class A(object):
        pass

    @App.method(App.func, a=A)
    def a_func(app, request):
        assert isinstance(app, App)
        return "A"

    app = App()
    assert app.func(A()) == "A"
    assert app.func(None) == "default"


def test_function_conflict():
    class app(morepath.App):
        @morepath.dispatch_method('a')
        def func(self, a):
            pass

    class A(object):
        pass

    @app.method(app.func, a=A)
    def a_func(app, a, request):
        pass

    @app.method(app.func, a=A)
    def a1_func(app, a, request):
        pass

    with pytest.raises(ConflictError):
        app.commit()


def test_function_no_conflict_different_apps():
    class base(morepath.App):
        @morepath.dispatch_method('a')
        def func(self, a):
            pass

    class app_a(base):
        pass

    class app_b(base):
        pass

    class A(object):
        pass

    @app_a.method(base.func, a=A)
    def a_func(app, a):
        pass

    @app_b.method(base.func, a=A)
    def a1_func(app, a):
        pass

    dectate.commit(app_a, app_b)


def test_run_app_with_context_without_it():
    class app(morepath.App):
        pass

        def __init__(self, mount_id):
            self.mount_id = mount_id

    with pytest.raises(TypeError):
        app()


def test_mapply_bug():
    c = Client(mapply_bug.app())

    response = c.get('/')

    assert response.body == b'the root'


def test_abbr_imperative():
    class app(morepath.App):
        pass

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

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Default view'

    response = c.get('/edit')
    assert response.body == b'Edit view'


def test_abbr_exception():
    class app(morepath.App):
        pass

    class Model(object):
        pass

    @app.path(path='/', model=Model)
    def get_model():
        return Model()

    try:
        with app.view(model=Model) as view:
            @view()
            def default(self, request):
                return "Default view"
            1 / 0

            @view(name='edit')
            def edit(self, request):
                return "Edit view"

    except ZeroDivisionError:
        pass

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Default view'

    # an exception happened halfway, so this one is never registered
    c.get('/edit', status=404)


def test_abbr_imperative2():
    class app(morepath.App):
        pass

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

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Default view'

    response = c.get('/edit')
    assert response.body == b'Edit view'


def test_abbr_nested():
    class app(morepath.App):
        pass

    class Model(object):
        pass

    @app.path(path='/', model=Model)
    def get_model():
        return Model()

    with app.view(model=Model) as view:
        @view()
        def default(self, request):
            return "Default"

        with view(name='extra') as view:
            @view()
            def get(self, request):
                return "Get"

            @view(request_method='POST')
            def post(self, request):
                return "Post"

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Default'

    response = c.get('/extra')
    assert response.body == b'Get'

    response = c.post('/extra')
    assert response.body == b'Post'


def test_function_directive():
    class app(morepath.App):
        @morepath.dispatch_method('o')
        def mygeneric(self, o):
            return "The object: %s" % o

    class Foo(object):
        def __init__(self, value):
            self.value = value

        def __repr__(self):
            return "<Foo with value: %s>" % self.value

    @app.method(app.mygeneric, o=Foo)
    def mygeneric_for_foo(app, o):
        return "The foo object: %s" % o

    a = app()

    assert a.mygeneric('blah') == 'The object: blah'
    assert a.mygeneric(Foo(1)) == (
        'The foo object: <Foo with value: 1>')


def test_classgeneric_function_directive():
    class app(morepath.App):
        @morepath.dispatch_method(reg.match_class('o'))
        def mygeneric(self, o):
            return "The object"

    class Foo(object):
        pass

    @app.method(app.mygeneric, o=Foo)
    def mygeneric_for_foo(app, o):
        return "The foo object"

    a = app()

    assert a.mygeneric(object) == 'The object'
    assert a.mygeneric(Foo) == 'The foo object'


def test_staticmethod():
    class App(morepath.App):
        pass

    @App.path('/')
    class Root(object):
        pass

    class A(object):
        @staticmethod
        @App.view(model=Root)
        def root_default(self, request):
            assert isinstance(self, Root)
            return "Hello world"

    c = Client(App())

    response = c.get('/')
    assert response.body == b'Hello world'


def test_classmethod_equivalent_to_staticmethod():
    class App(morepath.App):
        pass

    @App.path('/')
    class Root(object):
        pass

    class A(object):
        @classmethod
        @App.view(model=Root)
        def root_default(self, request):
            assert isinstance(self, Root)
            return "Hello world"

    c = Client(App())

    response = c.get('/')
    assert response.body == b'Hello world'


def test_classmethod_bound_outside():
    class App(morepath.App):
        pass

    @App.path('/')
    class Root(object):
        pass

    class A(object):
        @classmethod
        def root_default(cls, self, request):
            assert isinstance(self, Root)
            return "Hello world"

    App.view(model=Root)(A.root_default)

    c = Client(App())

    response = c.get('/')
    assert response.body == b'Hello world'


def test_instantiation_before_config():
    class App(morepath.App):
        pass

    # Typically, instantiating App would be done later, after the
    # decorators.  Since this use case has been found in the wild, we
    # might as well make sure it works:
    app = App()

    @App.path(path='')
    class Hello(object):
        pass

    @App.view(model=Hello)
    def hello_view(self, request):
        return 'hello'

    c = Client(app)

    response = c.get('/')
    assert response.body == b'hello'
