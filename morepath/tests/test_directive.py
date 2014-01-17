from .fixtures import basic, nested, abbr, mapply_bug
from morepath import setup
from morepath.error import ConflictError, MountError
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


def test_basic_testing_config():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.root()
    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='{id}',
               variables=lambda model: {'id': model.id})
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "The view for model: %s" % model.id

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    @app.view(model=Model, name='json', render=morepath.render_json)
    def json(request, model):
        return {'id': model.id}

    @app.view(model=Root)
    def root_default(request, model):
        return "The root: %s" % model.value

    @app.view(model=Root, name='link')
    def root_link(request, model):
        return request.link(model)

    config.commit()

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
    config = setup()
    app = morepath.App(testing_config=config)

    @app.root()
    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Root)
    def root_link(request, model):
        try:
            return request.link(Model('foo'))
        except LinkError:
            return "Link error"

    @app.view(model=Root, name='default')
    def root_link_with_default(request, model):
        return request.link(Model('foo'), default='hey')

    @app.view(model=Root, name='default2')
    def root_link_with_default2(request, model):
        return request.link(Model('foo'), default=('hey', dict(param=1)))

    config.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.data == 'Link error'
    response = c.get('/default')
    assert response.data == '/hey'
    response = c.get('/default2')
    assert response.data == '/hey?param=1'


def test_link_with_parameters():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.root()
    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    class Model(object):
        def __init__(self, id, param):
            self.id = id
            self.param = param

    @app.model(model=Model, path='{id}')
    def get_model(id, param=0):
        assert isinstance(param, int)
        return Model(id, param)

    @app.view(model=Model)
    def default(request, model):
        return "The view for model: %s %s" % (model.id, model.param)

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

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
    config = setup()
    app = morepath.App(testing_config=config)

    @app.root()
    class Root(object):
        def __init__(self, param=0):
            assert isinstance(param, int)
            self.param = param

    @app.view(model=Root)
    def default(request, model):
        return "The view for root: %s" % model.param

    @app.view(model=Root, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

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
    config = setup()
    app = morepath.App(testing_config=config)

    @app.root()
    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='{id}')
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "The view for model: %s" % model.id

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo/link')
    assert response.data == '/foo'


def test_implicit_parameters():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.root()
    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='foo')
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "The view for model: %s" % model.id

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

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
    config = setup()
    app = morepath.App(testing_config=config)

    @app.root()
    class Root(object):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='foo')
    def get_model(id='default'):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "The view for model: %s" % model.id

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

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
    config = setup()
    app = morepath.App(testing_config=config)

    @app.root()
    class Root(object):
        def __init__(self):
            self.value = 'ROOT'

    @app.view(model=Root)
    def default(request, model):
        1/0
        return ''

    config.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.status == '500 INTERNAL SERVER ERROR'


def test_simple_root():
    config = setup()
    app = morepath.App(testing_config=config)

    class Hello(object):
        pass

    hello = Hello()

    @app.root(model=Hello)
    def hello_model():
        return hello

    @app.view(model=Hello)
    def hello_view(request, model):
        return 'hello'

    config.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.data == 'hello'


def test_json_directive():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.model(path='{id}', variables=lambda model: {'id': model.id})
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.json(model=Model)
    def json(request, model):
        return {'id': model.id}

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == '{"id": "foo"}'


def test_redirect():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.root()
    class Root(object):
        def __init__(self):
            pass

    @app.view(model=Root, render=render_html)
    def default(request, model):
        return morepath.redirect('/')

    config.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.status == '302 FOUND'


def test_root_conflict():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.root()
    class Root(object):
        pass

    @app.root()
    class Something(object):
        pass

    with pytest.raises(ConflictError):
        config.commit()


def test_root_no_conflict_different_apps():
    config = setup()
    app_a = morepath.App(testing_config=config)
    app_b = morepath.App(testing_config=config)

    @app_a.root()
    class Root(object):
        pass

    @app_b.root()
    class Something(object):
        pass

    config.commit()


def test_model_conflict():
    config = setup()
    app = morepath.App(testing_config=config)

    class A(object):
        pass

    @app.model(model=A, path='a')
    def get_a():
        return A()

    @app.model(model=A, path='a')
    def get_a_again():
        return A()

    with pytest.raises(ConflictError):
        config.commit()


def test_path_conflict():
    config = setup()
    app = morepath.App(testing_config=config)

    class A(object):
        pass

    class B(object):
        pass

    @app.model(model=A, path='a')
    def get_a():
        return A()

    @app.model(model=B, path='a')
    def get_b():
        return B()

    with pytest.raises(ConflictError):
        config.commit()


def test_path_conflict_with_variable():
    config = setup()
    app = morepath.App(testing_config=config)

    class A(object):
        pass

    class B(object):
        pass

    @app.model(model=A, path='a/{id}')
    def get_a(id):
        return A()

    @app.model(model=B, path='a/{id2}')
    def get_b(id):
        return B()

    with pytest.raises(ConflictError):
        config.commit()

def test_path_conflict_with_variable_different_converters():
    config = setup()
    app = morepath.App(testing_config=config)

    class A(object):
        pass

    class B(object):
        pass

    @app.model(model=A, path='a/{id}', converters=Converter(decode=int))
    def get_a(id):
        return A()

    @app.model(model=B, path='a/{id}')
    def get_b(id):
        return B()

    with pytest.raises(ConflictError):
        config.commit()


def test_model_no_conflict_different_apps():
    config = setup()
    app_a = morepath.App(testing_config=config)

    class A(object):
        pass

    @app_a.model(model=A, path='a')
    def get_a():
        return A()

    app_b = morepath.App(testing_config=config)

    @app_b.model(model=A, path='a')
    def get_a_again():
        return A()

    config.commit()


def test_view_conflict():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        pass

    @app.view(model=Model, name='a')
    def a_view(request, model):
        pass

    @app.view(model=Model, name='a')
    def a1_view(request, model):
        pass

    with pytest.raises(ConflictError):
        config.commit()


def test_view_no_conflict_different_names():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        pass

    @app.view(model=Model, name='a')
    def a_view(request, model):
        pass

    @app.view(model=Model, name='b')
    def b_view(request, model):
        pass

    config.commit()


def test_view_no_conflict_different_predicates():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        pass

    @app.view(model=Model, name='a', request_method='GET')
    def a_view(request, model):
        pass

    @app.view(model=Model, name='a', request_method='POST')
    def b_view(request, model):
        pass

    config.commit()


def test_view_no_conflict_different_apps():
    config = setup()
    app_a = morepath.App(testing_config=config)
    app_b = morepath.App(testing_config=config)

    class Model(object):
        pass

    @app_a.view(model=Model, name='a')
    def a_view(request, model):
        pass

    @app_b.view(model=Model, name='a')
    def a1_view(request, model):
        pass

    config.commit()


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
    mounted = morepath.App('mounted')

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
    mounted = morepath.App('mounted')

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
    mounted = morepath.App('mounted', variables=['mount_id'])

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
    mounted = morepath.App('mounted', variables=['mount_id'])

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
    mounted = morepath.App('mounted', variables=['mount_id'])

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
    app = morepath.App('mounted', variables=['mount_id'])

    class Root(object):
        def __init__(self, mount_id):
            self.mount_id = mount_id

    def root_default(request, model):
        return "The root for mount id: %s" % model.mount_id

    c = setup()
    c.configurable(app)
    c.action(app.root(), Root)
    c.action(app.view(model=Root), root_default)
    c.commit()

    c = Client(app.mounted(mount_id='foo'), Response)

    response = c.get('/')
    assert response.data == 'The root for mount id: foo'


def test_mount_parent_link():
    app = morepath.App('app')
    class Model(object):
        def __init__(self, id):
            self.id = id

    mounted = morepath.App('mounted', variables=['mount_id'])

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
    mounted = morepath.App('mounted', variables=['mount_id'])

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
    mounted = morepath.App('mounted', variables=['mount_id'])

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
    app = morepath.App('app', variables=['mount_id'])

    c = setup()
    c.configurable(app)
    c.commit()

    c = Client(app, Response)
    with pytest.raises(MountError):
        c.get('/foo')


def test_mapply_bug():
    config = setup()
    config.scan(mapply_bug)
    config.commit()

    c = Client(mapply_bug.app, Response)

    response = c.get('/')

    assert response.data == 'the root'
