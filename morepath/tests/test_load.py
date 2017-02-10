import morepath
import pytest
from webtest import TestApp as Client


def test_load():
    class App(morepath.App):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    def load(request):
        return request.json

    @App.view(model=Root, request_method='POST', load=load)
    def root_post(self, request, obj):
        return "true" if obj == {'foo': 'bar'} else "false"

    app = App()
    client = Client(app)

    r = client.post_json('/', {'foo': 'bar'})

    assert r.body == b"true"


def test_load_requires_three_arguments():
    class App(morepath.App):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    def load(request):
        return request.json

    @App.view(model=Root, request_method='POST', load=load)
    def root_post(self, request):
        pass

    app = App()
    app.commit()

    client = Client(app)

    with pytest.raises(TypeError):
        client.post_json('/', {'foo': 'bar'})


def test_load_json():
    class App(morepath.App):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    def load(request):
        return request.json

    @App.json(model=Root, request_method='POST', load=load)
    def root_post(self, request, obj):
        return "true" if obj == {'foo': 'bar'} else "false"

    app = App()
    client = Client(app)

    r = client.post_json('/', {'foo': 'bar'})

    assert r.body == b'"true"'


def test_load_html():
    class App(morepath.App):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    def load(request):
        return request.json

    @App.html(model=Root, request_method='POST', load=load)
    def root_post(self, request, obj):
        return "true" if obj == {'foo': 'bar'} else "false"

    app = App()
    client = Client(app)

    r = client.post_json('/', {'foo': 'bar'})

    assert r.body == b"true"
