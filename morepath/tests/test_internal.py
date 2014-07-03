import morepath
from webtest import TestApp as Client


def setup_module(module):
    morepath.disable_implicit()


def test_internal():
    config = morepath.setup()

    class app(morepath.App):
        testing_config = config

    @app.path(path='')
    class Root(object):
        pass

    @app.json(model=Root)
    def root_default(self, request):
        return {'internal': request.view(self, name='internal')}

    @app.json(model=Root, name='internal', internal=True)
    def root_internal(self, request):
        return 'Internal!'

    config.commit()

    c = Client(app())

    response = c.get('/')

    assert response.body == b'{"internal": "Internal!"}'

    c.get('/internal', status=404)
