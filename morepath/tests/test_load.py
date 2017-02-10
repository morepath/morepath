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


def test_load_json_interaction():
    class App(morepath.App):
        pass

    @App.path(path='/')
    class Root(object):
        pass

    class A(object):
        pass

    class B(object):
        pass

    class Error(Exception):
        pass

    @App.load_json()
    def load_json(json, request):
        letter = json['letter']
        if letter == 'a':
            return A()
        elif letter == 'b':
            return B()
        else:
            raise Error()

    def load(request):
        return request.body_obj

    @App.json(model=Root, request_method='POST', load=load, body_model=A)
    def root_post_a(self, request, obj):
        assert request.body_obj is obj
        if isinstance(obj, A):
            return "this is a"
        assert False, "never reached"

    @App.json(model=Root, request_method='POST', load=load, body_model=B)
    def root_post_b(self, request, obj):
        assert request.body_obj is obj
        if isinstance(obj, B):
            return "this is b"
        assert False, "never reached"

    app = App()
    client = Client(app)

    r = client.post_json('/', {'letter': 'a'})
    assert r.json == "this is a"
    r = client.post_json('/', {'letter': 'b'})
    assert r.json == "this is b"
    with pytest.raises(Error):
        client.post_json('/', {'letter': 'c'})
