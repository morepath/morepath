import morepath
from morepath import setup_testing
from morepath.error import LinkError, ConflictError
from webtest import TestApp as Client
import pytest


def setup_module():
    morepath.disable_implicit()


def test_model_mount_conflict():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class app2(morepath.App):
        testing_config = config

    class A(object):
        pass

    @app.path(model=A, path='a')
    def get_a():
        return A()

    @app.mount(app=app2, path='a')
    def get_mount():
        return {}

    with pytest.raises(ConflictError):
        config.commit()


def test_mount():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        testing_config = config

    @mounted.path(path='')
    class MountedRoot(object):
        pass

    @mounted.view(model=MountedRoot)
    def root_default(self, request):
        return "The root"

    @mounted.view(model=MountedRoot, name='link')
    def root_link(self, request):
        return request.link(self)

    @app.mount(path='{id}', app=mounted)
    def get_context():
        return {}

    config.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The root'

    response = c.get('/foo/link')
    assert response.body == b'/foo'


def test_mount_empty_context_should_fail():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        testing_config = config

    @mounted.path(path='')
    class MountedRoot(object):
        pass

    @mounted.view(model=MountedRoot)
    def root_default(self, request):
        return "The root"

    @mounted.view(model=MountedRoot, name='link')
    def root_link(self, request):
        return request.link(self)

    @app.mount(path='{id}', app=mounted)
    def get_context():
        return None

    config.commit()

    c = Client(app())

    c.get('/foo', status=404)
    c.get('/foo/link', status=404)


def test_mount_context():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @mounted.path(path='')
    class MountedRoot(object):
        def __init__(self, mount_id):
            self.mount_id = mount_id

    @mounted.view(model=MountedRoot)
    def root_default(self, request):
        return "The root for mount id: %s" % self.mount_id

    @app.mount(path='{id}', app=mounted)
    def get_context(id):
        return {
            'mount_id': id
            }

    config.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The root for mount id: foo'
    response = c.get('/bar')
    assert response.body == b'The root for mount id: bar'


def test_mount_context_parameters():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @mounted.path(path='')
    class MountedRoot(object):
        def __init__(self, mount_id):
            assert isinstance(mount_id, int)
            self.mount_id = mount_id

    @mounted.view(model=MountedRoot)
    def root_default(self, request):
        return "The root for mount id: %s" % self.mount_id

    @app.mount(path='mounts', app=mounted)
    def get_context(mount_id=0):
        return {
            'mount_id': mount_id
            }

    config.commit()

    c = Client(app())

    response = c.get('/mounts?mount_id=1')
    assert response.body == b'The root for mount id: 1'
    response = c.get('/mounts')
    assert response.body == b'The root for mount id: 0'


def test_mount_context_parameters_empty_context():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @mounted.path(path='')
    class MountedRoot(object):
        # use a default parameter
        def __init__(self, mount_id='default'):
            self.mount_id = mount_id

    @mounted.view(model=MountedRoot)
    def root_default(self, request):
        return "The root for mount id: %s" % self.mount_id

    # the context creates an empty context.
    # this means the parameters are instead constructed from the
    # arguments of the MountedRoot constructor, and these
    # default to 'default', not a URL parameter
    @app.mount(path='{id}', app=mounted)
    def get_context(id):
        return {}

    config.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'The root for mount id: default'
    # the URL parameter mount_id cannot interfere with the mounting
    # process
    response = c.get('/bar?mount_id=blah')
    assert response.body == b'The root for mount id: default'


def test_mount_context_standalone():
    config = setup_testing()

    class app(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @app.path(path='')
    class Root(object):
        def __init__(self, mount_id):
            self.mount_id = mount_id

    @app.view(model=Root)
    def root_default(self, request):
        return "The root for mount id: %s" % self.mount_id

    config.commit()

    c = Client(app(mount_id='foo'))

    response = c.get('/')
    assert response.body == b'The root for mount id: foo'


def test_mount_parent_link():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    @app.path(path='models/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @mounted.path(path='')
    class MountedRoot(object):
        def __init__(self, mount_id):
            self.mount_id = mount_id

    @mounted.view(model=MountedRoot)
    def root_default(self, request):
        return request.parent.link(Model('one'))

    @app.mount(path='{id}', app=mounted)
    def get_context(id):
        return {
            'mount_id': id
            }

    config.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'/models/one'


def test_mount_child_link():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @mounted.path(path='models/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def app_root_default(self, request):
        return request.child(mounted, id='foo').link(Model('one'))

    @app.mount(path='{id}', app=mounted)
    def get_context(id):
        return {
            'mount_id': id
            }

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'/foo/models/one'


def test_mount_child_link_unknown_child():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @mounted.path(path='models/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def app_root_default(self, request):
        try:
            return request.child(mounted, id='foo').link(Model('one'))
        except LinkError:
            return 'link error'

    @app.mount(path='{id}', app=mounted)
    def get_context(id):
        # no child will be found ever
        return None

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'link error'


def test_mount_child_link_unknown_parent():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def app_root_default(self, request):
        try:
            return request.parent.link(Model('one'))
        except LinkError:
            return 'link error'

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'link error'


def test_mount_child_link_unknown_app():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @mounted.path(path='models/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def app_root_default(self, request):
        try:
            return request.child(mounted, id='foo').link(Model('one'))
        except LinkError:
            return "link error"

    # no mounting, so mounted is unknown when making link

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'link error'


def test_mount_repr():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @mounted.path(path='models/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def app_root_default(self, request):
        return repr(request.mounted.child(mounted, id='foo'))

    @app.mount(path='{id}', app=mounted)
    def get_context(id):
        return {
            'mount_id': id
            }

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body[:178] == (
        b"<morepath.Mount of <class "
        b"'morepath.tests.test_mount_directive.mounted'> with "
        b"variables: id='foo', "
        b"parent=<morepath.Mount of "
        b"<morepath.tests.test_mount_directive.app object at 0x")


def test_request_view_in_mount():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    @mounted.path(path='models/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @mounted.view(model=Model)
    def model_default(self, request):
        return {'hey': 'Hey'}

    @app.view(model=Root)
    def root_default(self, request):
        return request.child(mounted, id='foo').view(
            Model('x'))['hey']

    @app.mount(path='{id}', app=mounted)
    def get_context(id):
        return {
            'mount_id': id
            }

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Hey'


def test_request_view_in_mount_broken():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    @mounted.path(path='models/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @mounted.view(model=Model)
    def model_default(self, request):
        return {'hey': 'Hey'}

    @app.view(model=Root)
    def root_default(self, request):
        try:
            return request.child(mounted, id='foo').view(
                Model('x'))['hey']
        except LinkError:
            return "link error"

    # deliberately don't mount so using view is broken

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'link error'


def test_mount_implict_converters():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        testing_config = config

    class MountedRoot(object):
        def __init__(self, id):
            self.id = id

    @mounted.path(path='', model=MountedRoot)
    def get_root(id):
        return MountedRoot(id)

    @mounted.view(model=MountedRoot)
    def root_default(self, request):
        return "The root for: %s %s" % (self.id, type(self.id))

    @app.mount(path='{id}', app=mounted)
    def get_context(id=0):
        return {'id': id}

    config.commit()

    c = Client(app())

    response = c.get('/1')
    assert response.body in \
        (b"The root for: 1 <type 'int'>", b"The root for: 1 <class 'int'>")


def test_mount_explicit_converters():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        testing_config = config

    class MountedRoot(object):
        def __init__(self, id):
            self.id = id

    @mounted.path(path='', model=MountedRoot)
    def get_root(id):
        return MountedRoot(id)

    @mounted.view(model=MountedRoot)
    def root_default(self, request):
        return "The root for: %s %s" % (self.id, type(self.id))

    @app.mount(path='{id}', app=mounted, converters=dict(id=int))
    def get_context(id):
        return {'id': id}

    config.commit()

    c = Client(app())

    response = c.get('/1')
    assert response.body in \
        (b"The root for: 1 <type 'int'>", b"The root for: 1 <class 'int'>")


def test_mount_view_in_child_view():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class fooapp(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def default_homepage(self, request):
        return request.child(fooapp).view(FooRoot())

    @fooapp.path(path='')
    class FooRoot(object):
        pass

    @fooapp.view(model=FooRoot, name="name")
    def foo_name(self, request):
        return "Foo"

    @fooapp.view(model=FooRoot)
    def foo_default(self, request):
        return "Hello " + request.view(self, name="name")

    @app.mount(path="foo", app=fooapp)
    def mount_to_root():
        return {}

    config.commit()

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'Hello Foo'

    response = c.get('/')
    assert response.body == b'Hello Foo'


def test_mount_view_in_child_view_then_parent_view():
    config = setup_testing()

    class app(morepath.App):
        testing_config = config

    class fooapp(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def default_homepage(self, request):
        return (request.child(fooapp).view(FooRoot()) + ' ' +
                request.view(self, name='other'))

    @app.view(model=Root, name='other')
    def root_other(self, request):
        return 'other'

    @fooapp.path(path='')
    class FooRoot(object):
        pass

    @fooapp.view(model=FooRoot, name="name")
    def foo_name(self, request):
        return "Foo"

    @fooapp.view(model=FooRoot)
    def foo_default(self, request):
        return "Hello " + request.view(self, name="name")

    @app.mount(path="foo", app=fooapp)
    def mount_to_root():
        return {}

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'Hello Foo other'
