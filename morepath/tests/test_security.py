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
from webobtoolkit.client import Client, client_pipeline


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

    response = c.get('/foo')
    assert response.status == '401 Unauthorized'


def test_permission_directive():
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

    @app.permission(model=Model, permission=Permission)
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
    assert response.body == 'Model: foo'
    response = c.get('/bar')
    assert response.status == '401 Unauthorized'


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

    @app.permission(model=Model, permission=Permission, identity=None)
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
    assert response.body == 'Model: foo'
    response = c.get('/bar')
    assert response.status == '401 Unauthorized'


def test_policy_action():
    config = setup()
    config.scan(identity_policy)
    config.commit()

    c = Client(identity_policy.app)

    response = c.get('/foo')
    assert response.body == 'Model: foo'
    response = c.get('/bar')
    assert response.status == '401 Unauthorized'


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

    @app.permission(model=Model, permission=Permission)
    def get_permission(identity, model, permission):
        return identity.userid == 'user' and identity.password == 'secret'

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    config.commit()

    c = Client(app)

    response = c.get('/foo')
    assert response.status == '401 Unauthorized'

    headers = {'Authorization': 'Basic ' + base64.b64encode('user:wrong')}
    response = c.get('/foo', headers=headers)
    assert response.status == '401 Unauthorized'

    headers = {'Authorization': 'Basic ' + base64.b64encode('user:secret')}
    response = c.get('/foo', headers=headers)
    assert response.body == 'Model: foo'


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

    @app.permission(model=Model, permission=Permission)
    def get_permission(identity, model, permission):
        return identity.userid == 'user' and identity.password == u'sëcret'

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    config.commit()

    c = Client(app)

    response = c.get('/foo')
    assert response.status == '401 Unauthorized'

    headers = {'Authorization': 'Something'}
    response = c.get('/foo', headers=headers)
    assert response.status == '401 Unauthorized'

    headers = {'Authorization': 'Something other'}
    response = c.get('/foo', headers=headers)
    assert response.status == '401 Unauthorized'

    headers = {'Authorization': 'Basic ' + 'nonsense'}
    response = c.get('/foo', headers=headers)
    assert response.status == '401 Unauthorized'

    headers = {'Authorization': 'Basic ' + 'nonsense1'}
    response = c.get('/foo', headers=headers)
    assert response.status == '401 Unauthorized'

    # fallback to utf8
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(
            u'user:sëcret'.encode('utf8'))}
    response = c.get('/foo', headers=headers)
    assert response.body == 'Model: foo'

    # fallback to latin1
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(
            u'user:sëcret'.encode('latin1'))}
    response = c.get('/foo', headers=headers)
    assert response.body == 'Model: foo'

    # unknown encoding
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(
            u'user:sëcret'.encode('cp500'))}
    response = c.get('/foo', headers=headers)
    assert response.status == '401 Unauthorized'

    headers = {
        'Authorization': 'Basic ' + base64.b64encode(
            u'usersëcret'.encode('utf8'))}
    response = c.get('/foo', headers=headers)
    assert response.status == '401 Unauthorized'

    headers = {
        'Authorization': 'Basic ' + base64.b64encode(
            u'user:sëcret:'.encode('utf8'))}
    response = c.get('/foo', headers=headers)
    assert response.status == '401 Unauthorized'


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
        generic.remember(response, request, Identity('foo'),
                         lookup=request.lookup)
        return response

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    config.commit()

    c = Client(app)

    response = c.get('/foo')
    assert response.status == '200 OK'
    assert response.body == ''


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
        generic.forget(response, request, lookup=request.lookup)
        return response

    @app.identity_policy()
    def policy():
        return BasicAuthIdentityPolicy()

    config.commit()

    c = Client(app)

    response = c.get('/foo')
    assert response.status == '200 OK'
    assert response.body == ''

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
        data = json.loads(base64.b64decode(data))
        return Identity(**data)

    def remember(self, response, request, identity):
        data = base64.b64encode(json.dumps(identity.as_dict()))
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

    @app.permission(model=Model, permission=Permission)
    def get_permission(identity, model, permission):
        return identity.userid == 'user'

    @app.view(model=Model, permission=Permission)
    def default(self, request):
        return "Model: %s" % self.id

    @app.view(model=Model, name='log_in')
    def log_in(self, request):
        response = Response()
        generic.remember(response, request, Identity(userid='user',
                                                     payload='Amazing'),
                         lookup=request.lookup)
        return response

    @app.view(model=Model, name='log_out')
    def log_out(self, request):
        response = Response()
        generic.forget(response, request, lookup=request.lookup)
        return response

    @app.identity_policy()
    def policy():
        return DumbCookieIdentityPolicy()

    config.commit()

    c = Client(client_pipeline(app, cookie_support=True))

    response = c.get('/foo')
    assert response.status == '401 Unauthorized'

    response = c.get('/foo/log_in')

    response = c.get('/foo')
    assert response.status == '200 OK'
    assert response.body == 'Model: foo'

    response = c.get('/foo/log_out')

    response = c.get('/foo')
    assert response.status == '401 Unauthorized'
