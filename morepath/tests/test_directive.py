from .fixtures import basic, nested, abbr, mapply_bug
from morepath import setup
from morepath.error import ConflictError, ContextError
from morepath.config import Config
from morepath.request import Response
from morepath.view import render_html
from morepath.app import App
from morepath.converter import Converter
import morepath
from morepath.error import LinkError
import reg

from werkzeug.test import Client
import pytest


def test_basic():
    config = setup()
    config.scan(basic)
    config.commit()

    c = Client(basic.app, Response)

    response = c.get('/foo')

    assert response.data == 'The view for model: foo'

    response = c.get('/foo/link')
    assert response.data == '/foo'


def test_basic_json():
    config = setup()
    config.scan(basic)
    config.commit()

    c = Client(basic.app, Response)

    response = c.get('/foo/json')

    assert response.data == '{"id": "foo"}'


def test_basic_root():
    config = setup()
    config.scan(basic)
    config.commit()

    c = Client(basic.app, Response)

    response = c.get('/')

    assert response.data == 'The root: ROOT'

    # + is to make sure we get the view, not the sub-model as
    # the model is greedy
    response = c.get('/+link')
    assert response.data == '/'


def test_nested():
    config = setup()
    config.scan(nested)
    config.commit()

    c = Client(nested.outer_app, Response)

    response = c.get('/inner/foo')

    assert response.data == 'The view for model: foo'

    response = c.get('/inner/foo/link')
    assert response.data == '/inner/foo'


def test_abbr():
    config = setup()
    config.scan(abbr)
    config.commit()

    c = Client(abbr.app, Response)

    response = c.get('/foo')
    assert response.data == 'Default view: foo'

    response = c.get('/foo/edit')
    assert response.data == 'Edit view: foo'


def test_imperative():
    class Foo(object):
        pass

    @reg.generic
    def target():
        pass

    app = App()

    c = setup()
    foo = Foo()
    c.configurable(app)
    c.action(app.function(target), foo)
    c.commit()

    assert target.component(lookup=app.lookup()) is foo


def test_basic_imperative():
    app = morepath.App()

    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_model(id):
        return Model(id)

    def default(request, model):
        return "The view for model: %s" % model.id

    def link(request, model):
        return request.link(model)

    def json(request, model):
        return {'id': model.id}

    def root_default(request, model):
        return "The root: %s" % model.value

    def root_link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.root(), Root)
    c.action(app.model(model=Model, path='{id}',
                       variables=lambda model: {'id': model.id}),
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

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'The view for model: foo'

    response = c.get('/foo/link')
    assert response.data == '/foo'

    response = c.get('/foo/json')
    assert response.data == '{"id": "foo"}'

    response = c.get('/')
    assert response.data == 'The root: ROOT'

    # + is to make sure we get the view, not the sub-model
    response = c.get('/+link')
    assert response.data == '/'


def test_link_to_unknown_model():
    app = morepath.App()

    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id):
            self.id = id

    def root_link(request, model):
        try:
            return request.link(Model('foo'))
        except LinkError:
            return "Link error"

    def root_link_with_default(request, model):
        return request.link(Model('foo'), default='hey')

    def root_link_with_default2(request, model):
        return request.link(Model('foo'), default=('hey', dict(param=1)))

    c = setup()
    c.configurable(app)
    c.action(app.root(), Root)
    c.action(app.view(model=Root), root_link)
    c.action(app.view(model=Root, name='default'), root_link_with_default)
    c.action(app.view(model=Root, name='default2'), root_link_with_default2)
    c.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.data == 'Link error'
    response = c.get('/default')
    assert response.data == '/hey'
    response = c.get('/default2')
    assert response.data == '/hey?param=1'


def test_link_with_parameters():
    app = morepath.App()

    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id, param):
            self.id = id
            self.param = param

    def get_model(id, param=0):
        assert isinstance(param, int)
        return Model(id, param)

    def default(request, model):
        return "The view for model: %s %s" % (model.id, model.param)

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.root(), Root)
    c.action(app.model(model=Model, path='{id}',
                       variables=lambda model: {'id': model.id,
                                                'param': model.param}),
             get_model)
    c.action(app.view(model=Model),
             default)
    c.action(app.view(model=Model, name='link'),
             link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'The view for model: foo 0'

    response = c.get('/foo/link')
    assert response.data == '/foo?param=0'

    response = c.get('/foo?param=1')
    assert response.data == 'The view for model: foo 1'

    response = c.get('/foo/link?param=1')
    assert response.data == '/foo?param=1'


def test_root_link_with_parameters():
    app = morepath.App()

    class Root(object):
        def __init__(self, param=0):
            assert isinstance(param, int)
            self.param = param

    def default(request, model):
        return "The view for root: %s" % model.param

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.root(), Root)
    c.action(app.view(model=Root),
             default)
    c.action(app.view(model=Root, name='link'),
             link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.data == 'The view for root: 0'

    response = c.get('/link')
    assert response.data == '/?param=0'

    response = c.get('/?param=1')
    assert response.data == 'The view for root: 1'

    response = c.get('/link?param=1')
    assert response.data == '/?param=1'


def test_implicit_variables():
    app = morepath.App()

    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_model(id):
        return Model(id)

    def default(request, model):
        return "The view for model: %s" % model.id

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.root(), Root)
    c.action(app.model(model=Model, path='{id}'),
             get_model)
    c.action(app.view(model=Model),
             default)
    c.action(app.view(model=Model, name='link'),
             link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo/link')
    assert response.data == '/foo'


def test_implicit_parameters():
    app = morepath.App()

    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_model(id):
        return Model(id)

    def default(request, model):
        return "The view for model: %s" % model.id

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.root(), Root)
    c.action(app.model(model=Model, path='foo'),
             get_model)
    c.action(app.view(model=Model),
             default)
    c.action(app.view(model=Model, name='link'),
             link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'The view for model: None'
    response = c.get('/foo?id=bar')
    assert response.data == 'The view for model: bar'
    response = c.get('/foo/link')
    assert response.data == '/foo?id=None'
    response = c.get('/foo/link?id=bar')
    assert response.data == '/foo?id=bar'


def test_implicit_parameters_default():
    app = morepath.App()

    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    def get_model(id='default'):
        return Model(id)

    def default(request, model):
        return "The view for model: %s" % model.id

    def link(request, model):
        return request.link(model)

    c = setup()
    c.configurable(app)
    c.action(app.root(), Root)
    c.action(app.model(model=Model, path='foo'),
             get_model)
    c.action(app.view(model=Model),
             default)
    c.action(app.view(model=Model, name='link'),
             link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'The view for model: default'
    response = c.get('/foo?id=bar')
    assert response.data == 'The view for model: bar'
    response = c.get('/foo/link')
    assert response.data == '/foo?id=default'
    response = c.get('/foo/link?id=bar')
    assert response.data == '/foo?id=bar'


def test_convert_exception_to_internal_error():
    app = morepath.App()

    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    def default(request, model):
        1/0
        return ''

    c = setup()
    c.configurable(app)
    c.action(app.root(), Root)
    c.action(app.view(model=Root), default)
    c.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.status == '500 INTERNAL SERVER ERROR'


def test_simple_root():
    app = morepath.App()

    class Hello(object):
        pass

    hello = Hello()

    def hello_model():
        return hello

    def hello_view(request, model):
        return 'hello'

    c = setup()
    c.configurable(app)
    c.action(app.root(model=Hello), hello_model)
    c.action(app.view(model=Hello),
             hello_view)
    c.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.data == 'hello'


def test_json_directive():
    app = morepath.App()

    class Model(object):
        def __init__(self, id):
            self.id = id

    def default(request, model):
        return "The view for model: %s" % model.id

    def json(request, model):
        return {'id': model.id}

    c = setup()
    c.configurable(app)
    c.action(app.model(path='{id}',
                       variables=lambda model: {'id': model.id}),
             Model)
    c.action(app.json(model=Model),
             json)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == '{"id": "foo"}'


def test_redirect():
    app = morepath.App()

    class Root(object):
        def __init__(self):
            pass

    def default(request, model):
        return morepath.redirect('/')

    c = setup()
    c.configurable(app)
    c.action(app.root(),
             Root)
    c.action(app.view(model=Root, render=render_html),
             default)
    c.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.status == '302 FOUND'


def test_root_conflict():
    app = morepath.App()

    a = app.root()

    @a
    class Root(object):
        pass

    b = app.root()

    @b
    class Something(object):
        pass

    c = Config()
    c.configurable(app)
    c.action(a, Root)
    c.action(b, Something)

    with pytest.raises(ConflictError):
        c.commit()


def test_root_no_conflict_different_apps():
    app_a = morepath.App()
    app_b = morepath.App()

    a = app_a.root()

    @a
    class Root(object):
        pass

    b = app_b.root()

    @b
    class Something(object):
        pass

    c = Config()
    c.configurable(app_a)
    c.configurable(app_b)
    c.action(a, Root)
    c.action(b, Something)
    c.commit()


def test_model_conflict():
    app = morepath.App()

    class A(object):
        pass

    a = app.model(model=A, path='a')

    @a
    def get_a():
        return A()

    b = app.model(model=A, path='a')

    @b
    def get_a_again():
        return A()

    c = Config()
    c.configurable(app)
    c.action(a, get_a)
    c.action(b, get_a_again)

    with pytest.raises(ConflictError):
        c.commit()


def test_path_conflict():
    app = morepath.App()

    class A(object):
        pass

    class B(object):
        pass

    a = app.model(model=A, path='a')

    @a
    def get_a():
        return A()

    b = app.model(model=B, path='a')

    @b
    def get_b():
        return B()

    c = Config()
    c.configurable(app)
    c.action(a, get_a)
    c.action(b, get_b)

    with pytest.raises(ConflictError):
        c.commit()


def test_path_conflict_with_variable():
    app = morepath.App()

    class A(object):
        pass

    class B(object):
        pass

    a = app.model(model=A, path='a/{id}')

    @a
    def get_a(id):
        return A()

    b = app.model(model=B, path='a/{id2}')

    @b
    def get_b(id):
        return B()

    c = Config()
    c.configurable(app)
    c.action(a, get_a)
    c.action(b, get_b)

    with pytest.raises(ConflictError):
        c.commit()

def test_path_conflict_with_variable_different_converters():
    app = morepath.App()

    class A(object):
        pass

    class B(object):
        pass

    a = app.model(model=A, path='a/{id}', converters=Converter(decode=int))

    @a
    def get_a(id):
        return A()

    b = app.model(model=B, path='a/{id}')

    @b
    def get_b(id):
        return B()

    c = Config()
    c.configurable(app)
    c.action(a, get_a)
    c.action(b, get_b)

    with pytest.raises(ConflictError):
        c.commit()


def test_model_no_conflict_different_apps():
    app_a = morepath.App()

    class A(object):
        pass

    a = app_a.model(model=A, path='a')

    @a
    def get_a():
        return A()

    app_b = morepath.App()

    b = app_b.model(model=A, path='a')

    @b
    def get_a_again():
        return A()

    c = Config()
    c.configurable(app_a)
    c.configurable(app_b)
    c.action(a, get_a)
    c.action(b, get_a_again)
    c.commit()


def test_view_conflict():
    app = morepath.App()

    class Model(object):
        pass

    a = app.view(model=Model, name='a')
    a1 = app.view(model=Model, name='a')

    @a
    def a_view(request, model):
        pass

    @a1
    def a1_view(request, model):
        pass

    c = Config()
    c.configurable(app)
    c.action(a, a_view)
    c.action(a1, a1_view)

    with pytest.raises(ConflictError):
        c.commit()


def test_view_no_conflict_different_names():
    app = morepath.App()

    class Model(object):
        pass

    a = app.view(model=Model, name='a')
    b = app.view(model=Model, name='b')

    @a
    def a_view(request, model):
        pass

    @b
    def b_view(request, model):
        pass

    c = Config()
    c.configurable(app)
    c.action(a, a_view)
    c.action(b, b_view)
    c.commit()


def test_view_no_conflict_different_predicates():
    app = morepath.App()

    class Model(object):
        pass

    a = app.view(model=Model, name='a', request_method='GET')
    b = app.view(model=Model, name='a', request_method='POST')

    @a
    def a_view(request, model):
        pass

    @b
    def b_view(request, model):
        pass

    c = Config()
    c.configurable(app)
    c.action(a, a_view)
    c.action(b, b_view)
    c.commit()


def test_view_no_conflict_different_apps():
    app_a = morepath.App()
    app_b = morepath.App()

    class Model(object):
        pass

    a = app_a.view(model=Model, name='a')
    a1 = app_b.view(model=Model, name='a')

    @a
    def a_view(request, model):
        pass

    @a1
    def a1_view(request, model):
        pass

    c = Config()
    c.configurable(app_a)
    c.configurable(app_b)
    c.action(a, a_view)
    c.action(a1, a1_view)
    c.commit()


def test_view_conflict_with_json():
    app = morepath.App()

    class Model(object):
        pass

    a = app.view(model=Model, name='a')
    a1 = app.json(model=Model, name='a')

    @a
    def a_view(request, model):
        pass

    @a1
    def a1_view(request, model):
        pass

    c = Config()
    c.configurable(app)
    c.action(a, a_view)
    c.action(a1, a1_view)

    with pytest.raises(ConflictError):
        c.commit()


def test_view_conflict_with_html():
    app = morepath.App()

    class Model(object):
        pass

    a = app.view(model=Model, name='a')
    a1 = app.html(model=Model, name='a')

    @a
    def a_view(request, model):
        pass

    @a1
    def a1_view(request, model):
        pass

    c = Config()
    c.configurable(app)
    c.action(a, a_view)
    c.action(a1, a1_view)

    with pytest.raises(ConflictError):
        c.commit()


def test_function_conflict():
    app = morepath.App()

    def func(a):
        pass

    class A(object):
        pass

    a = app.function(func, A)

    @a
    def a_func(arequest, model):
        pass

    a1 = app.function(func, A)

    @a1
    def a1_func(request, model):
        pass

    c = Config()
    c.configurable(app)
    c.action(a, a_func)
    c.action(a1, a1_func)

    with pytest.raises(ConflictError):
        c.commit()


def test_function_no_conflict_different_apps():
    app_a = morepath.App()
    app_b = morepath.App()

    def func(a):
        pass

    class A(object):
        pass

    a = app_a.function(func, A)
    a1 = app_b.function(func, A)

    @a
    def a_func(a):
        pass

    @a1
    def a1_func(a):
        pass

    c = Config()
    c.configurable(app_a)
    c.configurable(app_b)
    c.action(a, a_func)
    c.action(a1, a1_func)
    c.commit()


def test_mount():
    app = morepath.App('app')
    mounted = morepath.App('mounted', context=[])

    class MountedRoot(object):
        pass

    def root_default(request, model):
        return "The root"

    def root_link(request, model):
        return request.link(model)

    def get_context():
        return {}

    c = setup()
    c.configurable(app)
    c.configurable(mounted)
    c.action(app.mount(path='{id}', app=mounted), get_context)
    c.action(mounted.root(), MountedRoot)
    c.action(mounted.view(model=MountedRoot),
             root_default)
    c.action(mounted.view(model=MountedRoot, name='link'),
             root_link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'The root'

    response = c.get('/foo/link')
    assert response.data == '/foo'


def test_mount_empty_context():
    app = morepath.App('app')
    mounted = morepath.App('mounted', context=[])

    class MountedRoot(object):
        pass

    def root_default(request, model):
        return "The root"

    def root_link(request, model):
        return request.link(model)

    def get_context():
        pass

    c = setup()
    c.configurable(app)
    c.configurable(mounted)
    c.action(app.mount(path='{id}', app=mounted), get_context)
    c.action(mounted.root(), MountedRoot)
    c.action(mounted.view(model=MountedRoot),
             root_default)
    c.action(mounted.view(model=MountedRoot, name='link'),
             root_link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'The root'

    response = c.get('/foo/link')
    assert response.data == '/foo'


def test_mount_context():
    app = morepath.App('app')
    mounted = morepath.App('mounted', context=['mount_id'])

    class MountedRoot(object):
        def __init__(self, mount_id):
            self.mount_id = mount_id

    def root_default(request, model):
        return "The root for mount id: %s" % model.mount_id

    def get_context(id):
        return {
            'mount_id': id
            }

    c = setup()
    c.configurable(app)
    c.configurable(mounted)
    c.action(app.mount(path='{id}', app=mounted), get_context)
    c.action(mounted.root(), MountedRoot)
    c.action(mounted.view(model=MountedRoot), root_default)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'The root for mount id: foo'
    response = c.get('/bar')
    assert response.data == 'The root for mount id: bar'


def test_mount_context_parameters():
    app = morepath.App('app')
    mounted = morepath.App('mounted', context=['mount_id'])

    class MountedRoot(object):
        def __init__(self, mount_id):
            assert isinstance(mount_id, int)
            self.mount_id = mount_id

    def root_default(request, model):
        return "The root for mount id: %s" % model.mount_id

    def get_context(mount_id=0):
        return {
            'mount_id': mount_id
            }

    c = setup()
    c.configurable(app)
    c.configurable(mounted)
    c.action(app.mount(path='mounts', app=mounted), get_context)
    c.action(mounted.root(), MountedRoot)
    c.action(mounted.view(model=MountedRoot), root_default)
    c.commit()

    c = Client(app, Response)

    response = c.get('/mounts?mount_id=1')
    assert response.data == 'The root for mount id: 1'
    response = c.get('/mounts')
    assert response.data == 'The root for mount id: 0'


def test_mount_context_parameters_empty_context():
    app = morepath.App('app')
    mounted = morepath.App('mounted', context=['mount_id'])

    class MountedRoot(object):
        # use a default parameter
        def __init__(self, mount_id='default'):
            self.mount_id = mount_id

    def root_default(request, model):
        return "The root for mount id: %s" % model.mount_id

    # the context does not in fact construct the context.
    # this means the parameters are instead constructed from the
    # arguments of the MountedRoot constructor, and these
    # default to 'default'
    def get_context(id):
        return {
            }

    c = setup()
    c.configurable(app)
    c.configurable(mounted)
    c.action(app.mount(path='{id}', app=mounted), get_context)
    c.action(mounted.root(), MountedRoot)
    c.action(mounted.view(model=MountedRoot), root_default)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'The root for mount id: default'
    # the URL parameter mount_id cannot interfere with the mounting
    # process
    response = c.get('/bar?mount_id=blah')
    assert response.data == 'The root for mount id: default'

def test_mount_context_standalone():
    mounted = morepath.App('mounted', context=['mount_id'])

    class MountedRoot(object):
        def __init__(self, mount_id):
            self.mount_id = mount_id

    def root_default(request, model):
        return "The root for mount id: %s" % model.mount_id

    c = setup()
    c.configurable(mounted)
    c.action(mounted.root(), MountedRoot)
    c.action(mounted.view(model=MountedRoot), root_default)
    c.commit()

    c = Client(mounted.context(mount_id='foo'), Response)

    response = c.get('/')
    assert response.data == 'The root for mount id: foo'


def test_mount_parent_link():
    app = morepath.App('app')
    class Model(object):
        def __init__(self, id):
            self.id = id

    mounted = morepath.App('mounted', context=['mount_id'])

    class MountedRoot(object):
        def __init__(self, mount_id):
            self.mount_id = mount_id

    def root_default(request, model):
        return request.link(Model('one'), mounted=request.mounted().parent())

    def get_context(id):
        return {
            'mount_id': id
            }

    c = setup()
    c.configurable(app)
    c.configurable(mounted)
    c.action(app.model(path='models/{id}',
                       variables=lambda m: {'id': m.id}),
             Model)
    c.action(app.mount(path='{id}', app=mounted), get_context)
    c.action(mounted.root(), MountedRoot)
    c.action(mounted.view(model=MountedRoot), root_default)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == '/models/one'


def test_mount_child_link():
    app = morepath.App('app')
    mounted = morepath.App('mounted', context=['mount_id'])

    class Model(object):
        def __init__(self, id):
            self.id = id

    class Root(object):
        pass

    def app_root_default(request, model):
        return request.link(
            Model('one'),
            mounted=request.mounted().child(mounted, id='foo'))

    def get_context(id):
        return {
            'mount_id': id
            }

    c = setup()
    c.configurable(app)
    c.configurable(mounted)
    c.action(mounted.model(path='models/{id}',
                           variables=lambda m: {'id': m.id}),
             Model)
    c.action(app.mount(path='{id}', app=mounted), get_context)
    c.action(app.root(), Root)
    c.action(app.view(model=Root), app_root_default)
    c.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.data == '/foo/models/one'


def test_request_view_in_mount():
    app = morepath.App('app')
    mounted = morepath.App('mounted', context=['mount_id'])

    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    def model_default(request, model):
        return {'hey': 'Hey'}

    def root_default(request, model):
        return request.view(
            Model('x'), mounted=request.mounted().child(
                mounted, mount_id='foo'))['hey']

    def get_context(id):
        return {
            'mount_id': id
            }

    c = setup()
    c.configurable(app)
    c.configurable(mounted)
    c.action(app.root(), Root)
    c.action(app.view(model=Root), root_default)
    c.action(app.mount(path='{id}', app=mounted), get_context)
    c.action(mounted.model(path='models/{id}',
                           variables=lambda m: {'id': m.id}),
             Model)
    c.action(mounted.view(model=Model), model_default)
    c.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.data == 'Hey'


def test_run_app_with_context_without_it():
    app = morepath.App('app', context=['mount_id'])

    c = setup()
    c.configurable(app)
    c.commit()

    c = Client(app, Response)
    with pytest.raises(ContextError):
        c.get('/foo')


def test_mapply_bug():
    config = setup()
    config.scan(mapply_bug)
    config.commit()

    c = Client(mapply_bug.app, Response)

    response = c.get('/')

    assert response.data == 'the root'
