from .fixtures import basic, nested
from morepath import setup
from morepath.error import ConflictError
from morepath.config import Config
from morepath.request import Response
from morepath.view import render_html
from morepath.app import App
import morepath
import reg

from werkzeug.test import Client
import pytest


def test_basic():
    setup()
    basic.app.clear()

    config = Config()
    config.scan(basic)
    config.commit()

    c = Client(basic.app, Response)

    response = c.get('/foo')

    assert response.data == 'The view for model: foo'

    response = c.get('/foo/link')
    assert response.data == 'foo'


def test_basic_json():
    setup()
    basic.app.clear()

    config = Config()
    config.scan(basic)
    config.commit()

    c = Client(basic.app, Response)

    response = c.get('/foo/json')

    assert response.data == '{"id": "foo"}'


def test_basic_root():
    setup()
    basic.app.clear()

    config = Config()
    config.scan(basic)
    config.commit()

    c = Client(basic.app, Response)

    response = c.get('/')

    assert response.data == 'The root: ROOT'

    # + is to make sure we get the view, not the sub-model as
    # the model is greedy
    response = c.get('/+link')
    assert response.data == ''


def test_nested():
    setup()
    nested.outer_app.clear()
    nested.app.clear()

    config = Config()
    config.scan(nested)
    config.commit()

    c = Client(nested.outer_app, Response)

    response = c.get('/inner/foo')

    assert response.data == 'The view for model: foo'

    response = c.get('/inner/foo/link')
    assert response.data == 'inner/foo'


def test_imperative():
    setup()

    class Foo(object):
        pass

    @reg.generic
    def target():
        pass

    app = App()

    c = Config()
    c.action(app, app)
    foo = Foo()
    c.action(app.function(target), foo)
    c.commit()

    assert target.component(lookup=app.lookup()) is foo


def test_basic_imperative():
    setup()

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

    c = Config()
    c.action(app, app)
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
    assert response.data == 'foo'

    response = c.get('/foo/json')
    assert response.data == '{"id": "foo"}'

    response = c.get('/')
    assert response.data == 'The root: ROOT'

    # + is to make sure we get the view, not the sub-model
    response = c.get('/+link')
    assert response.data == ''


def test_json_directive():
    setup()

    app = morepath.App()

    class Model(object):
        def __init__(self, id):
            self.id = id

    def default(request, model):
        return "The view for model: %s" % model.id

    def json(request, model):
        return {'id': model.id}

    c = Config()
    c.action(app, app)
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
    setup()

    app = morepath.App()

    class Root(object):
        def __init__(self):
            pass

    def default(request, model):
        return morepath.redirect('/')

    c = Config()
    c.action(app, app)
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
    c.action(a, get_a)
    c.action(b, get_b)

    with pytest.raises(ConflictError):
        c.commit()


def test_no_path_conflict_with_variable_different_converters():
    app = morepath.App()

    class A(object):
        pass

    class B(object):
        pass

    a = app.model(model=A, path='a/{id:int}')

    @a
    def get_a(id):
        return A()

    b = app.model(model=B, path='a/{id:str}')

    @b
    def get_b(id):
        return B()

    c = Config()
    c.action(a, get_a)
    c.action(b, get_b)

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
    c.action(a, a_func)
    c.action(a1, a1_func)
    c.commit()


def test_mount():
    setup()

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

    c = Config()
    c.action(app, app)
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
    assert response.data == 'foo'


def test_mount_context():
    setup()

    app = morepath.App('app')
    mounted = morepath.App('mounted')

    class MountedRoot(object):
        def __init__(self, mount_id):
            self.mount_id = mount_id

    def get_mounted_root(mount_id):
        return MountedRoot(mount_id)

    def root_default(request, model):
        return "The root for mount id: %s" % model.mount_id

    def get_context(id):
        return {
            'mount_id': id
            }

    c = Config()
    c.action(app, app)
    c.action(app.mount(path='{id}', app=mounted), get_context)
    c.action(mounted.root(), MountedRoot)
    c.action(mounted.view(model=MountedRoot), root_default)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'The root for mount id: foo'
    response = c.get('/bar')
    assert response.data == 'The root for mount id: bar'


def test_mount_context_standalone():
    setup()

    mounted = morepath.App('mounted')

    class MountedRoot(object):
        def __init__(self, mount_id):
            self.mount_id = mount_id

    def get_mounted_root(mount_id):
        return MountedRoot(mount_id)

    def root_default(request, model):
        return "The root for mount id: %s" % model.mount_id

    c = Config()
    c.action(mounted.root(), MountedRoot)
    c.action(mounted.view(model=MountedRoot), root_default)
    c.commit()

    c = Client(mounted.context({'mount_id': 'foo'}), Response)

    response = c.get('/')
    assert response.data == 'The root for mount id: foo'
