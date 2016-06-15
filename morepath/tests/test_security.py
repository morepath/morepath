# -*- coding: utf-8 -*-
import pytest

import morepath
from morepath.request import Response
from morepath import generic
from morepath.authentication import Identity, NO_IDENTITY
from .fixtures import identity_policy
import base64
import json
from webtest import TestApp as Client
try:
    from cookielib import CookieJar
except ImportError:
    from http.cookiejar import CookieJar


def setup_module(module):
    morepath.disable_implicit()


def test_no_permission():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.path(model=Model, path='{id}',
              variables=lambda model: {'id': model.id})
    def get_model(id):
        return Model(id)

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    c = Client(app())

    c.get('/foo', status=403)


def test_permission_directive_identity():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.verify_identity()
    def verify_identity(identity):
        return True

    @app.path(model=Model, path='{id}',
              variables=lambda model: {'id': model.id})
    def get_model(id):
        return Model(id)

    @app.permission_rule(model=Model, permission=Permission)
    def get_permission(identity, model, permission):
        if model.id == 'foo':
            return True
        else:
            return False

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.identity_policy()
    class IdentityPolicy(object):
        def identify(self, request):
            return Identity('testidentity')

        def remember(self, response, request, identity):
            pass

        def forget(self, response, request):
            pass

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'Model: foo'
    response = c.get('/bar', status=403)


def test_permission_directive_no_identity():
    class app(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.path(model=Model, path='{id}',
              variables=lambda model: {'id': model.id})
    def get_model(id):
        return Model(id)

    @app.permission_rule(model=Model, permission=Permission, identity=None)
    def get_permission(identity, model, permission):
        if model.id == 'foo':
            return True
        else:
            return False

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    c = Client(app())

    response = c.get('/foo')
    assert response.body == b'Model: foo'
    response = c.get('/bar', status=403)


def test_policy_action():
    c = Client(identity_policy.app())

    response = c.get('/foo')
    assert response.body == b'Model: foo'
    response = c.get('/bar', status=403)


class DumbCookieIdentityPolicy(object):
    """A very insecure cookie-based policy.

    Only for testing. Don't use in practice!
    """
    def identify(self, request):
        data = request.cookies.get('dumb_id', None)
        if data is None:
            return NO_IDENTITY
        data = json.loads(base64.b64decode(data).decode())
        return Identity(**data)

    def remember(self, response, request, identity):
        data = base64.b64encode(str.encode(json.dumps(identity.as_dict())))
        response.set_cookie('dumb_id', data)

    def forget(self, response, request):
        response.delete_cookie('dumb_id')


def test_cookie_identity_policy():
    class app(morepath.App):
        pass

    @app.path(path='{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.permission_rule(model=Model, permission=Permission)
    def get_permission(identity, model, permission):
        return identity.userid == 'user'

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.view(model=Model, name='log_in')
    def log_in(self, request):
        response = Response()
        request.app.remember_identity(
            response, request, Identity(userid='user', payload='Amazing'))
        return response

    @app.view(model=Model, name='log_out')
    def log_out(self, request):
        response = Response()
        request.app.forget_identity(response, request)
        return response

    @app.identity_policy()
    def policy():
        return DumbCookieIdentityPolicy()

    @app.verify_identity()
    def verify_identity(identity):
        return True

    c = Client(app(), cookiejar=CookieJar())

    response = c.get('/foo', status=403)

    response = c.get('/foo/log_in')

    response = c.get('/foo', status=200)
    assert response.body == b'Model: foo'

    response = c.get('/foo/log_out')

    response = c.get('/foo', status=403)


def test_default_verify_identity():
    class app(morepath.App):
        pass

    identity = morepath.Identity('foo')

    assert not generic.verify_identity(identity, lookup=app().lookup)


def test_verify_identity_directive():
    class app(morepath.App):
        pass

    @app.verify_identity()
    def verify_identity(identity):
        return identity.password == 'right'

    identity = morepath.Identity('foo', password='wrong')
    assert not generic.verify_identity(identity, lookup=app().lookup)
    identity = morepath.Identity('foo', password='right')
    assert generic.verify_identity(identity, lookup=app().lookup)


def test_false_verify_identity():
    class app(morepath.App):
        pass

    @app.path(path='{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.view(model=Model, name='log_in')
    def log_in(self, request):
        response = Response()
        with pytest.deprecated_call():
            generic.remember_identity(
                response, request,
                Identity(userid='user', payload='Amazing'),
                lookup=request.lookup)
        return response

    @app.identity_policy()
    def policy():
        return DumbCookieIdentityPolicy()

    @app.verify_identity()
    def verify_identity(identity):
        return False

    c = Client(app(), cookiejar=CookieJar())

    c.get('/foo', status=403)

    c.get('/foo/log_in')

    c.get('/foo', status=403)


def test_settings():
    class App(morepath.App):
        pass

    class Model(object):
        pass

    @App.verify_identity()
    def verify_identity(identity):
        return True

    @App.path(model=Model, path='test')
    def get_model():
        return Model()

    @App.view(model=Model)
    def default(self, request):
        return "%s, your token is valid." % request.identity.userid

    @App.setting_section(section="test")
    def get_test_settings():
        return {'encryption_key': 'secret'}

    @App.identity_policy()
    def get_identity_policy(settings):
        test_settings = settings.test.__dict__.copy()
        return IdentityPolicy(**test_settings)

    class IdentityPolicy(object):
        def __init__(self, encryption_key):
            self.encryption_key = encryption_key

        def identify(self, request):
            token = self.get_token(request)
            if token is None or not self.token_is_valid(
                token, self.encryption_key
            ):
                return NO_IDENTITY
            return Identity('Testuser')

        def remember(self, response, request, identity):
            pass

        def forget(self, response, request):
            pass

        def get_token(self, request):
            try:
                authtype, token = request.authorization
            except ValueError:
                return None
            if authtype.lower() != 'bearer':
                return None
            return token

        def token_is_valid(self, token, encryption_key):
            return token == encryption_key  # fake validation

    c = Client(App())

    headers = {'Authorization': 'Bearer secret'}
    response = c.get('/test', headers=headers)
    assert response.body == b'Testuser, your token is valid.'


def test_prevent_poisoned_host_headers():

    class App(morepath.App):
        pass

    @App.path(path='')
    class Model(object):
        pass

    @App.view(model=Model)
    def view_model(self, request):
        return 'ok'

    poisoned_hosts = (
        'example.com@evil.tld',
        'example.com:dr.frankenstein@evil.tld',
        'example.com:dr.frankenstein@evil.tld:80',
        'example.com:80/badpath',
        'example.com: recovermypassword.com',
    )

    legit_hosts = (
        'example.com',
        'example.com:80',
        '12.34.56.78',
        '12.34.56.78:443',
        '[2001:19f0:feee::dead:beef:cafe]',
        '[2001:19f0:feee::dead:beef:cafe]:8080',
        'xn--4ca9at.com',  # Punnycode for öäü.com
    )

    c = Client(App())

    for host in legit_hosts:
        response = c.get('/', headers={'Host': host})
        assert response.status_code == 200

    for host in poisoned_hosts:
        response = c.get('/', headers={'Host': host}, expect_errors=True)
        assert response.status_code == 400
