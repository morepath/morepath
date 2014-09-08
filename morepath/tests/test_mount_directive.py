import morepath
from morepath import setup
from morepath.error import LinkError, ConflictError
from webtest import TestApp as Client
import pytest


def setup_module():
    morepath.disable_implicit()


def test_model_mount_conflict():
    config = setup()

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
    config = setup()

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
    config = setup()

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
    config = setup()

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
    config = setup()

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
    config = setup()

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
    config = setup()

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
    config = setup()

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
    config = setup()

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


def test_mount_sibling_link():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class first(morepath.App):
        testing_config = config

    class second(morepath.App):
        testing_config = config

    @first.path(path='models/{id}')
    class FirstModel(object):
        def __init__(self, id):
            self.id = id

    @first.view(model=FirstModel)
    def first_model_default(self, request):
        return request.sibling('second').link(SecondModel(2))

    @second.path(path='foos/{id}')
    class SecondModel(object):
        def __init__(self, id):
            self.id = id

    @app.path(path='')
    class Root(object):
        pass

    @app.mount(path='first', app=first)
    def get_context_first():
        return {}

    @app.mount(path='second', app=second)
    def get_context_second():
        return {}

    config.commit()

    c = Client(app())

    response = c.get('/first/models/1')
    assert response.body == b'/second/foos/2'


def test_mount_sibling_link_at_root_app():
    config = setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    class Item(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Root)
    def root_default(self, request):
        return request.sibling('foo').link(Item(3))

    config.commit()

    c = Client(app())

    with pytest.raises(LinkError):
        response = c.get('/')


def test_mount_child_link_unknown_child():
    config = setup()

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
    config = setup()

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
    config = setup()

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


def test_request_view_in_mount():
    config = setup()

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


def test_request_linkmaker_child_child():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    class submounted(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    @app.view(model=Root)
    def root_default(self, request):
        return request.child(mounted, id='foo').child(submounted).view(
            SubRoot())

    @app.view(model=Root, name='info')
    def root_info(self, request):
        return 'info'

    @app.mount(path='{id}', app=mounted)
    def get_context(id):
        return {
            'mount_id': id
            }

    @mounted.mount(path='sub', app=submounted)
    def get_context2():
        return {}

    @submounted.path(path='')
    class SubRoot(object):
        pass

    @submounted.view(model=SubRoot)
    def subroot_default(self, request):
        return "SubRoot"

    @submounted.view(model=SubRoot, name='parentage')
    def subroot_parentage(self, request):
        return request.parent.parent.view(Root(), name='info')
    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'SubRoot'

    response = c.get('/foo/sub/parentage')
    assert response.body == b'info'


def test_request_view_in_mount_broken():
    config = setup()

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

    @app.view(model=Root, name='doublechild')
    def doublechild(self, request):
        try:
            return request.child(mounted, id='foo').child(
                mounted, id='bar').link(Model('x'))
        except LinkError:
            return 'link error'

    @app.view(model=Root, name='childparent')
    def childparent(self, request):
        try:
            return request.child(mounted, id='foo').parent.link(Model('x'))
        except LinkError:
            return 'link error'

    # deliberately don't mount so using view is broken

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'link error'

    response = c.get('/doublechild')
    assert response.body == b'link error'

    response = c.get('/childparent')
    assert response.body == b'link error'


def test_mount_implict_converters():
    config = setup()

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
    config = setup()

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
    config = setup()

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
    config = setup()

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


def test_mount_directive_with_link_and_absorb():
    config = setup()

    class app1(morepath.App):
        testing_config = config

    @app1.path(path="")
    class Model1(object):
        pass

    class app2(morepath.App):
        testing_config = config

    class Model2(object):
        def __init__(self, absorb):
            self.absorb = absorb

    @app2.path(model=Model2, path='', absorb=True)
    def get_model(absorb):
        return Model2(absorb)

    @app2.view(model=Model2)
    def default(self, request):
        return "A:%s L:%s" % (self.absorb, request.link(self))

    @app1.mount(path="foo", app=app2)
    def get_mount():
        return {}

    config.commit()

    c = Client(app1())

    response = c.get('/foo')
    assert response.body == b'A: L:/foo'

    response = c.get('/foo/bla')
    assert response.body == b'A:bla L:/foo/bla'


def test_mount_named_child_link_explicit_name():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
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
        return request.child(mounted).link(Model('one'))

    @app.view(model=Root, name='extra')
    def app_root_default2(self, request):
        return request.child('sub').link(Model('one'))

    @app.mount(path='subapp', app=mounted, name='sub')
    def get_context():
        return {}

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'/subapp/models/one'

    response = c.get('/extra')
    assert response.body == b'/subapp/models/one'


def test_mount_named_child_link_name_defaults_to_path():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
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
        return request.child(mounted).link(Model('one'))

    @app.view(model=Root, name='extra')
    def app_root_default2(self, request):
        return request.child('subapp').link(Model('one'))

    @app.mount(path='subapp', app=mounted)
    def get_context():
        return {}

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'/subapp/models/one'

    response = c.get('/extra')
    assert response.body == b'/subapp/models/one'


def test_named_mount_with_parameters():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    @mounted.path(path='')
    class MountedRoot(object):
        def __init__(self, mount_id):
            assert isinstance(mount_id, int)
            self.mount_id = mount_id

    @mounted.view(model=MountedRoot)
    def root_default(self, request):
        return "The root for mount id: %s" % self.mount_id

    @app.mount(path='mounts/{mount_id}', app=mounted)
    def get_context(mount_id=0):
        return {
            'mount_id': mount_id
            }

    class Item(object):
        def __init__(self, id):
            self.id = id

    @mounted.path(path='items/{id}', model=Item)
    def get_item(id):
        return Item(id)

    @app.view(model=Root, path='/')
    def root_default(self, request):
        return request.child('mounts/{mount_id}', mount_id=3).link(Item(4))

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'/mounts/3/items/4'


def test_named_mount_with_url_parameters():
    config = setup()

    class app(morepath.App):
        testing_config = config

    class mounted(morepath.App):
        variables = ['mount_id']
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

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

    class Item(object):
        def __init__(self, id):
            self.id = id

    @mounted.path(path='items/{id}', model=Item)
    def get_item(id):
        return Item(id)

    @app.view(model=Root, path='/')
    def root_default(self, request):
        return request.child('mounts', mount_id=3).link(Item(4))

    config.commit()

    c = Client(app())

    response = c.get('/')
    assert response.body == b'/mounts/items/4?mount_id=3'
