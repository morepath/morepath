import morepath
from webtest import TestApp as Client
from morepath.error import LinkError
import pytest


def setup_module(module):
    morepath.disable_implicit()


def test_defer_links():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

    @root.path(path='')
    class RootModel(object):
        pass

    @root.view(model=RootModel)
    def root_model_default(self, request):
        return request.link(SubModel())

    @sub.path(path='')
    class SubModel(object):
        pass

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    @root.defer_links(model=SubModel)
    def defer_links_sub_model(obj):
        return sub()

    config.commit()

    c = Client(root())

    response = c.get('/')
    assert response.body == b'/sub'


def test_defer_view():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

    @root.path(path='')
    class RootModel(object):
        pass

    @root.json(model=RootModel)
    def root_model_default(self, request):
        return request.view(SubModel())

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.json(model=SubModel)
    def submodel_default(self, request):
        return {'hello': 'world'}

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    @root.defer_links(model=SubModel)
    def defer_links_sub_model(obj):
        return sub()

    config.commit()

    c = Client(root())

    response = c.get('/')
    assert response.json == {'hello': 'world'}


def test_defer_view_predicates():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

    @root.path(path='')
    class RootModel(object):
        pass

    @root.json(model=RootModel)
    def root_model_default(self, request):
        return request.view(SubModel(), name='edit')

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.json(model=SubModel, name='edit')
    def submodel_edit(self, request):
        return {'hello': 'world'}

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    @root.defer_links(model=SubModel)
    def defer_links_sub_model(obj):
        return sub()

    config.commit()

    c = Client(root())

    response = c.get('/')
    assert response.json == {'hello': 'world'}


def test_defer_view_missing_view():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

    @root.path(path='')
    class RootModel(object):
        pass

    @root.json(model=RootModel)
    def root_model_default(self, request):
        return {'not_found': request.view(SubModel(), name='unknown')}

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.json(model=SubModel, name='edit')
    def submodel_edit(self, request):
        return {'hello': 'world'}

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    @root.defer_links(model=SubModel)
    def defer_links_sub_model(obj):
        return sub()

    config.commit()

    c = Client(root())

    response = c.get('/')
    assert response.json == {'not_found': None}


def test_defer_links_mount_parameters():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

        def __init__(self, name):
            self.name = name

    @root.path(path='')
    class RootModel(object):
        pass

    @root.view(model=RootModel)
    def root_model_default(self, request):
        return request.link(SubModel('foo'))

    class SubModel(object):
        def __init__(self, name):
            self.name = name

    @sub.path(path='', model=SubModel)
    def get_sub_model(request):
        return SubModel(request.app.name)

    @root.mount(app=sub, path='{mount_name}',
                variables=lambda a: {'mount_name': a.name})
    def mount_sub(mount_name):
        return sub(name=mount_name)

    @root.defer_links(model=SubModel)
    def defer_links_sub_model(obj):
        return sub(name=obj.name)

    config.commit()

    c = Client(root())

    response = c.get('/')
    assert response.body == b'/foo'


def test_defer_link_acquisition():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

    @root.path(path='model/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @root.view(model=Model)
    def model_default(self, request):
        return "Hello"

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.view(model=SubModel)
    def sub_model_default(self, request):
        return request.link(Model('foo'))

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    @sub.defer_links(model=Model)
    def get_parent(obj):
        return None

    config.commit()

    c = Client(root())

    response = c.get('/sub')
    assert response.body == b'/model/foo'


def test_defer_view_acquisition():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

    @root.path(path='model/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @root.json(model=Model)
    def model_default(self, request):
        return {"Hello": "World"}

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.json(model=SubModel)
    def sub_model_default(self, request):
        return request.view(Model('foo'))

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    @sub.defer_links(model=Model)
    def get_parent(obj):
        return None

    config.commit()

    c = Client(root())

    response = c.get('/sub')
    assert response.json == {"Hello": "World"}


def test_defer_link_acquisition_blocking():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

    @root.path(path='model/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @root.view(model=Model)
    def model_default(self, request):
        return "Hello"

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.view(model=SubModel)
    def sub_model_default(self, request):
        try:
            return request.link(Model('foo'))
        except LinkError:
            return "link error"

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    # no defer_links_to_parent

    config.commit()

    c = Client(root())

    response = c.get('/sub')
    assert response.body == b'link error'


def test_defer_view_acquisition_blocking():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

    @root.path(path='model/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @root.json(model=Model)
    def model_default(self, request):
        return {"Hello": "World"}

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.json(model=SubModel)
    def sub_model_default(self, request):
        return request.view(Model('foo')) is None

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    # no defer_links_to_parent

    config.commit()

    c = Client(root())

    response = c.get('/sub')
    assert response.json is True


def test_defer_link_should_not_cause_web_views_to_exist():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

    @root.path(path='')
    class Model(object):
        pass

    @root.view(model=Model)
    def model_default(self, request):
        return "Hello"

    @root.view(model=Model, name='extra')
    def model_extra(self, request):
        return "Extra"

    # note inheritance from model. we still don't
    # want the extra view to show up on the web
    @sub.path(path='')
    class SubModel(Model):
        pass

    @sub.view(model=SubModel)
    def sub_model_default(self, request):
        return request.link(Model())

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    @sub.defer_links(model=Model)
    def get_parent(obj):
        return None

    config.commit()

    c = Client(root())

    response = c.get('/sub')
    assert response.body == b'/'

    c.get('/sub/+extra', status=404)


def test_defer_link_to_parent_from_root():
    config = morepath.setup()

    class root(morepath.App):
        testing_config = config

    class sub(morepath.App):
        testing_config = config

    @root.path(path='')
    class Model(object):
        pass

    class OtherModel(object):
        pass

    @root.view(model=Model)
    def model_default(self, request):
        return request.link(OtherModel())

    @root.defer_links(model=OtherModel)
    def get_parent(obj):
        return None

    config.commit()

    c = Client(root())

    with pytest.raises(LinkError):
        response = c.get('/')
