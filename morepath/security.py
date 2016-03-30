import binascii
import base64
from reg import mapply

from .compat import bytes_
from .app import RegRegistry
from .settings import SettingRegistry


class NoIdentity(object):
    userid = None


NO_IDENTITY = NoIdentity()


class IdentityPolicyRegistry(object):
    factory_arguments = {
        'reg_registry': RegRegistry,
        'setting_registry': SettingRegistry,
    }

    def __init__(self, reg_registry, setting_registry):
        self.reg_registry = reg_registry
        self.setting_registry = setting_registry
        self.identity_policy = None

    def register_identity_policy_function(self, obj, dispatch, name):
        # make sure we only have a single identity policy
        identity_policy = self.identity_policy
        if identity_policy is None:
            self.identity_policy = identity_policy = mapply(
                obj,
                settings=self.setting_registry)
        self.reg_registry.register_function(
            dispatch,
            getattr(identity_policy, name))


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
        self.verified = None  # starts out as never verified

    def as_dict(self):
        """Export identity as dictionary.

        This includes the userid and the extra keyword parameters used
        when the identity was created.

        :returns: dict with identity info.
        """
        result = {'userid': self.userid}
        for name in self._names:
            result[name] = getattr(self, name)
        return result


class IdentityPolicy(object):
    """Identity policy API.

    Implement this API if you want to have a custom way to establish
    identities for users in your application.
    """

    def identify(self, request):
        """Establish what identity this user claims to have from request.

        :param request: Request to extract identity information from.
        :type request: :class:`morepath.Request`.
        :returns: :class:`morepath.security.Identity` instance or
          :attr:`morepath.security.NO_IDENTITY` if identity cannot
          be established.
        """
        raise NotImplementedError()  # pragma: nocoverage

    def remember(self, response, request, identity):
        """Remember identity on response.

        Implements ``morepath.remember_identity``, which is called
        from user login code.

        Given an identity object, store it on the response, for
        instance as a cookie. Some policies may not do any storing but
        instead retransmit authentication information each time in the
        request. Basic authentication is an example of such a
        non-storing policy.

        :param response: response object on which to store identity.
        :type response: :class:`morepath.Response`
        :param request: request object.
        :type request: :class:`morepath.Request`
        :param identity: identity to remember.
        :type identity: :class:`morepath.security.Identity`

        """
        raise NotImplementedError()  # pragma: nocoverage

    def forget(self, response, request):
        """Forget identity on response.

        Implements ``morepath.forget_identity``, which is called from
        user logout code.

        Remove identifying information from the response. This could
        delete a cookie or issue a basic auth re-authentication.

        :param response: response object on which to forget identity.
        :type response: :class:`morepath.Response`
        :param request: request object.
        :type request: :class:`morepath.Request`

        """
        raise NotImplementedError()  # pragma: nocoverage


class BasicAuthIdentityPolicy(object):
    """Identity policy that uses HTTP Basic Authentication.
    """
    def __init__(self, realm='Realm'):
        self.realm = realm

    def identify(self, request):
        """Establish claimed identity using request.

        :param request: Request to extract identity information from.
        :type request: :class:`morepath.Request`.
        :returns: :class:`morepath.security.Identity` instance.
        """
        try:
            authorization = request.authorization
        except ValueError:
            return None
        if authorization is None:
            return None
        authtype, params = authorization
        auth = parse_basic_auth(authtype, params)
        if auth is None:
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
        response.headers.add('WWW-Authenticate',
                             'Basic realm="%s"' % self.realm)


class BasicAuthInfo(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password


# code taken from
# pyramid.authentication.BasicAuthenticationPolicy._get_credentials
def parse_basic_auth(authtype, params):
    # try:
    #     authtype, params = parse_auth(value)
    # except ValueError:
    #     return None

    if authtype != 'Basic':
        return None
    try:
        authbytes = b64decode(params.strip())
    except (TypeError, binascii.Error):  # can't decode
        return None

    # try utf-8 first, then latin-1; see discussion in
    # https://github.com/Pylons/pyramid/issues/898
    try:
        auth = authbytes.decode('utf-8')
    except UnicodeDecodeError:
        # might get nonsense but normally not get decode error
        auth = authbytes.decode('latin-1')

    try:
        username, password = auth.split(':', 1)
    except ValueError:  # not enough values to unpack
        return None

    return BasicAuthInfo(username, password)


def b64decode(v):
    return base64.b64decode(bytes_(v))
