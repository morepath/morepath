import morepath
from webtest import TestApp as Client


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

    @root.defer_links(model=SubModel, app=sub)
    def defer_links_sub_model(obj):
        return {}

    config.commit()

    c = Client(root())

    response = c.get('/')
    assert response.body == b'/sub'


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

    @root.defer_links(model=SubModel, app=sub)
    def defer_links_sub_model(obj):
        return {'name': obj.name}

    config.commit()

    c = Client(root())

    response = c.get('/')
    assert response.body == b'/foo'
