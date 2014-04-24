# -*- coding: utf-8 -*-
import morepath
from morepath import setup
from morepath.request import Response
from morepath import generic
from morepath.security import (Identity, BasicAuthIdentityPolicy,
                               NO_IDENTITY)
from .fixtures import identity_policy
import base64
import json
from webtest import TestApp as Client
try:
    from cookielib import CookieJar
except ImportError:
    from http.cookiejar import CookieJar
from webob.exc import HTTPForbidden

def setup_module(module):
    morepath.disable_implicit()


def test_no_permission():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    c.get('/foo', status=403)


def test_permission_directive():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/foo')
    assert response.body == b'Model: foo'
    response = c.get('/bar', status=403)


def test_permission_directive_no_identity():
    config = setup()
    app = morepath.App(testing_config=config)

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

    config.commit()

    c = Client(app)

    response = c.get('/foo')
    assert response.body == b'Model: foo'
    response = c.get('/bar', status=403)


def test_policy_action():
    config = setup()
    config.scan(identity_policy)
    config.commit()

    c = Client(identity_policy.app)

    response = c.get('/foo')
    assert response.body == b'Model: foo'
    response = c.get('/bar', status=403)


def test_basic_auth_identity_policy():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.path(model=Model, path='{id}',
              variables=lambda model: {'id': model.id})
    def get_model(id):
        return Model(id)

    @app.permission_rule(model=Model, permission=Permission)
    def get_permission(identity, model, permission):
        return identity.userid == 'user' and identity.password == 'secret'

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    @app.verify_identity()
    def verify_identity(identity):
        return True

    @app.view(model=HTTPForbidden)
    def make_unauthorized(self, request):
        @request.after
        def set_status_code(response):
            response.status_code = 401
        return "Unauthorized"

    config.commit()

    c = Client(app)

    response = c.get('/foo', status=401)

    headers = {'Authorization': 'Basic ' + str(base64.b64encode(b'user:wrong').decode())}
    response = c.get('/foo', headers=headers, status=401)

    headers = {'Authorization': 'Basic ' + str(base64.b64encode(b'user:secret').decode())}
    response = c.get('/foo', headers=headers)
    assert response.body == b'Model: foo'


def test_basic_auth_identity_policy_errors():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    class Permission(object):
        pass

    @app.path(model=Model, path='{id}',
              variables=lambda model: {'id': model.id})
    def get_model(id):
        return Model(id)

    @app.permission_rule(model=Model, permission=Permission)
    def get_permission(identity, model, permission):
        return identity.userid == 'user' and identity.password == u'sëcret'

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    @app.verify_identity()
    def verify_identity(identity):
        return True

    config.commit()

    c = Client(app)

    response = c.get('/foo', status=403)

    headers = {'Authorization': 'Something'}
    response = c.get('/foo', headers=headers, status=403)

    headers = {'Authorization': 'Something other'}
    response = c.get('/foo', headers=headers, status=403)

    headers = {'Authorization': 'Basic ' + 'nonsense'}
    response = c.get('/foo', headers=headers, status=403)

    headers = {'Authorization': 'Basic ' + 'nonsense1'}
    response = c.get('/foo', headers=headers, status=403)

    # fallback to utf8
    headers = {
        'Authorization': 'Basic ' + str(base64.b64encode(
            u'user:sëcret'.encode('utf8')).decode())}
    response = c.get('/foo', headers=headers)
    assert response.body == b'Model: foo'

    # fallback to latin1
    headers = {
        'Authorization': 'Basic ' + str(base64.b64encode(
            u'user:sëcret'.encode('latin1')).decode())}
    response = c.get('/foo', headers=headers)
    assert response.body == b'Model: foo'

    # unknown encoding
    headers = {
        'Authorization': 'Basic ' + str(base64.b64encode(
            u'user:sëcret'.encode('cp500')).decode())}
    response = c.get('/foo', headers=headers, status=403)

    headers = {
        'Authorization': 'Basic ' + str(base64.b64encode(
            u'usersëcret'.encode('utf8')).decode())}
    response = c.get('/foo', headers=headers, status=403)

    headers = {
        'Authorization': 'Basic ' + str(base64.b64encode(
            u'user:sëcret:'.encode('utf8')).decode())}
    response = c.get('/foo', headers=headers, status=403)


def test_basic_auth_remember():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.path(path='{id}',
              variables=lambda model: {'id': model.id})
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Model)
    def default(self, request):
        # will not actually do anything as it's a no-op for basic
        # auth, but at least won't crash
        response = Response()
        generic.remember_identity(response, request, Identity('foo'),
                                  lookup=request.lookup)
        return response

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    config.commit()

    c = Client(app)

    response = c.get('/foo', status=200)
    assert response.body == b''


def test_basic_auth_forget():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.path(path='{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.view(model=Model)
    def default(self, request):
        # will not actually do anything as it's a no-op for basic
        # auth, but at least won't crash
        response = Response(content_type='text/plain')
        generic.forget_identity(response, request, lookup=request.lookup)
        return response

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    config.commit()

    c = Client(app)

    response = c.get('/foo', status=200)
    assert response.body == b''

    assert sorted(response.headers.items()) == [
        ('Content-Length', '0'),
        ('Content-Type', 'text/plain; charset=UTF-8'),
        ('WWW-Authenticate', 'Basic realm="Realm"'),
        ]


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
    config = setup()
    app = morepath.App(testing_config=config)

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
        generic.remember_identity(response, request,
                                  Identity(userid='user',
                                           payload='Amazing'),
                                  lookup=request.lookup)
        return response

    @app.view(model=Model, name='log_out')
    def log_out(self, request):
        response = Response()
        generic.forget_identity(response, request, lookup=request.lookup)
        return response

    @app.identity_policy()
    def policy():
        return DumbCookieIdentityPolicy()

    @app.verify_identity()
    def verify_identity(identity):
        return True

    config.commit()

    c = Client(app, cookiejar=CookieJar())

    response = c.get('/foo', status=403)

    response = c.get('/foo/log_in')

    response = c.get('/foo', status=200)
    assert response.body == b'Model: foo'

    response = c.get('/foo/log_out')

    response = c.get('/foo', status=403)


def test_default_verify_identity():
    config = setup()
    app = morepath.App(testing_config=config)
    config.commit()

    identity = morepath.Identity('foo')

    assert not generic.verify_identity(identity, lookup=app.lookup)


def test_verify_identity_directive():
    config = setup()
    app = morepath.App(testing_config=config)

    @app.verify_identity()
    def verify_identity(identity):
        return identity.password == 'right'

    config.commit()
    identity = morepath.Identity('foo', password='wrong')
    assert not generic.verify_identity(identity, lookup=app.lookup)
    identity = morepath.Identity('foo', password='right')
    assert generic.verify_identity(identity, lookup=app.lookup)
