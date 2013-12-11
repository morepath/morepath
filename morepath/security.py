from .request import Request
from morepath import generic
from werkzeug import parse_authorization_header

class NoIdentity(object):
    userid = None


NO_IDENTITY = NoIdentity()


class Identity(object):
    def __init__(self, userid, **kw):
        self.userid = userid
        for key, value in kw.items():
            setattr(self, key, value)


def register_identity_policy(app, policy):
    # XXX instead should issue sub directives in identity policy directive
    app.register(generic.identify, [Request], policy.identify)
    app.register(generic.remember, [Request, object], policy.remember)
    app.register(generic.forget, [Request], policy.forget)


class BasicAuthIdentityPolicy(object):
    def __init__(self, realm='Realm'):
        self.realm = realm

    def identify(self, request):
        header = request.headers.get('Authorization')
        if header is None:
            return None
        auth = parse_authorization_header(header)
        if auth is None:
            return None
        if auth.password is None:
            # not basic auth
            return None
        return Identity(userid=auth.username, password=auth.password)

    def remember(self, request, identity):
        return []

    def forget(self, request):
        # XXX werkzeug provides WWWAuthenticate helper class; is
        # this something to use or not?
        return [('WWW-Authenticate', 'Basic realm="%s"' % self.realm)]


def register_permission_checker(registry, identity, model, permission, func):
    registry.register(generic.permits, (identity, model, permission), func)


# XXX request.user property
