from morepath import generic
from werkzeug import parse_authorization_header


class NoIdentity(object):
    userid = None


NO_IDENTITY = NoIdentity()


class Identity(object):
    """Claimed identity of a user.

    Note that this identity is just a claim; to authenticate the user
    and authorize them you need to implement Morepath permission directives.
    """
    def __init__(self, userid, **kw):
        """
        :param userid: The userid of this identity
        :param kw: Extra information to store in identity.
        """
        self.userid = userid
        self._names = kw.keys()
        for key, value in kw.items():
            setattr(self, key, value)

    def as_dict(self):
        """Export identity as dictionary.

        This includes the userid and the extra keyword parameters used
        when the identity was created.

        :returns: dict with identity info.
        """
        result = {
            'userid': self.userid,
            }
        for name in self._names:
            result[name] = getattr(self, name)
        return result


class BasicAuthIdentityPolicy(object):
    """Identity policy that uses HTTP Basic Authentication.

    Note that this policy does **not** do any password validation. You're
    expected to do so using permission directives.
    """
    def __init__(self, realm='Realm'):
        self.realm = realm

    def identify(self, request):
        """Establish claimed identity using request.

        :param request: Request to extract identity information from.
        :type request: :class:`morepath.Request`.
        :returns: :class:`morepath.security.Identity` instance.
        """
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
        """Remember identity on response.

        This is a no-op for basic auth, as the browser re-identifies
        upon each request in that case.

        :param response: response object on which to store identity.
        :type response: :class:`morepath.Response`
        :param request: request object.
        :type request: :class:`morepath.Request`
        :param identity: identity to remember.
        :type identity: :class:`morepath.security.Identity`
        """

    def forget(self, response, request):
        """Forget identity on response.

        This causes the browser to issue a basic authentication
        dialog.  Warning: for basic auth, the browser in fact does not
        forget the information even if ``forget`` is called.

        :param response: response object on which to forget identity.
        :type response: :class:`morepath.Response`
        :param request: request object.
        :type request: :class:`morepath.Request`

        """
        # XXX werkzeug provides WWWAuthenticate helper class; is
        # this something to use or not? but if so, how?
        response.headers.add('WWW-Authenticate',
                             'Basic realm="%s"' % self.realm)


def register_permission_checker(registry, identity, model, permission, func):
    registry.register(generic.permits, (identity, model, permission), func)


# XXX request.user property
