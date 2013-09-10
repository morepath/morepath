from .fixtures import basic, nested
from morepath import setup
from morepath.config import Config
from morepath.request import Response
from morepath.app import App
from comparch import Interface
import morepath

from werkzeug.test import Client


def test_basic():
    setup()
    basic.app.clear()

    config = Config()
    config.scan(basic)
    config.app(basic.app)
    config.commit()

    c = Client(basic.app, Response)

    response = c.get('/foo')

    assert response.data == 'The resource for model: foo'

    response = c.get('/foo/link')
    assert response.data == 'foo'


def test_basic_json():
    setup()
    basic.app.clear()

    config = Config()
    config.scan(basic)
    config.app(basic.app)
    config.commit()

    c = Client(basic.app, Response)

    response = c.get('/foo/json')

    assert response.data == '{"id": "foo"}'


def test_basic_root():
    setup()
    basic.app.clear()

    config = Config()
    config.scan(basic)
    config.app(basic.app)
    config.commit()

    c = Client(basic.app, Response)

    response = c.get('/')

    assert response.data == 'The root: ROOT'

    # @@ is to make sure we get the view, not the sub-model
    response = c.get('/@@link')
    assert response.data == ''


def test_nested():
    setup()
    nested.outer_app.clear()
    nested.app.clear()

    config = Config()
    config.scan(nested)
    config.app(nested.outer_app)
    config.app(nested.app)
    config.commit()

    c = Client(nested.outer_app, Response)

    response = c.get('/inner/foo')

    assert response.data == 'The resource for model: foo'

    response = c.get('/inner/foo/link')
    assert response.data == 'inner/foo'


def test_imperative():
    setup()

    class Foo(object):
        pass

    class ITarget(Interface):
        pass

    app = App()

    c = Config()
    c.app(app)
    foo = Foo()
    c.action(app.component(ITarget, []), foo)
    c.commit()

    assert ITarget.component(lookup=app.lookup()) is foo


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
        return "The resource for model: %s" % model.id

    def link(request, model):
        return request.link(model)

    def json(request, model):
        return {'id': model.id}

    def root_default(request, model):
        return "The root: %s" % model.value

    def root_link(request, model):
        return request.link(model)

    c = Config()
    c.app(app)
    c.action(app.root(), Root)
    c.action(app.model(model=Model, path='{id}',
                       variables=lambda model: {'id': model.id}),
             get_model)
    c.action(app.resource(model=Model),
             default)
    c.action(app.resource(model=Model, name='link'),
             link)
    c.action(app.resource(model=Model, name='json',
                          render=morepath.render_json),
             json)
    c.action(app.resource(model=Root),
             root_default)
    c.action(app.resource(model=Root, name='link'),
             root_link)
    c.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'The resource for model: foo'

    response = c.get('/foo/link')
    assert response.data == 'foo'

    response = c.get('/foo/json')
    assert response.data == '{"id": "foo"}'

    response = c.get('/')
    assert response.data == 'The root: ROOT'

    # @@ is to make sure we get the view, not the sub-model
    response = c.get('/@@link')
    assert response.data == ''
