from .request import Request, Response
from morepath import generic
from werkzeug import parse_authorization_header

class NoIdentity(object):
    userid = None


NO_IDENTITY = NoIdentity()


class Identity(object):
    def __init__(self, userid, **kw):
        self.userid = userid
        self._names = kw.keys()
        for key, value in kw.items():
            setattr(self, key, value)

    def as_dict(self):
        result = {
            'userid': self.userid,
            }
        for name in self._names:
            result[name] = getattr(self, name)
        return result

def register_identity_policy(app, policy):
    # XXX instead should issue sub directives in identity policy directive
    app.register(generic.identify, [Request], policy.identify)
    app.register(generic.remember, [Response, Request, object], policy.remember)
    app.register(generic.forget, [Response, Request], policy.forget)


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

    def remember(self, response, request, identity):
        pass

    def forget(self, response, request):
        # XXX werkzeug provides WWWAuthenticate helper class; is
        # this something to use or not? but if so, how?
        response.headers.add('WWW-Authenticate',
                             'Basic realm="%s"' % self.realm)


def register_permission_checker(registry, identity, model, permission, func):
    registry.register(generic.permits, (identity, model, permission), func)


# XXX request.user property
