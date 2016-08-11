"""This module defines the authentication system of Morepath.

Authentication is done by establishing an identity for a request using
an identity policy registered by the :meth:`morepath.App.identity_policy`
directive.

:data:`morepath.NO_IDENTITY`, :class:`morepath.Identity`,
:class:`morepath.IdentityPolicy` are part of the public API.

See also :class:`morepath.directive.IdentityPolicyRegistry`
"""
import abc

from .compat import with_metaclass


class NoIdentity(object):
    """The user is not yet logged in.

    The request is anonymous.
    """
    userid = None


NO_IDENTITY = NoIdentity()
"""The identity if the request is anonymous.

The user has not yet logged in.
"""


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
        """The user ID of the identity.

        May be ``None`` if no particular identity was established."""
        self._names = kw.keys()
        for key, value in kw.items():
            setattr(self, key, value)
        self.verified = None  # starts out as never verified

    def as_dict(self):
        """Export identity as dictionary.

        This includes the userid and the extra keyword parameters used
        when the identity was created.

        :return: dict with identity info.
        """
        result = {'userid': self.userid}
        for name in self._names:
            result[name] = getattr(self, name)
        return result


class IdentityPolicy(with_metaclass(abc.ABCMeta)):
    """Identity policy API.

    Implement this API if you want to have a custom way to establish
    identities for users in your application.
    """

    @abc.abstractmethod
    def identify(self, request):
        """Establish what identity this user claims to have from request.

        :param request: Request to extract identity information from.
        :type request: :class:`morepath.Request`.
        :return: :class:`morepath.Identity` instance or
          :attr:`morepath.NO_IDENTITY` if identity cannot
          be established.
        """

    @abc.abstractmethod
    def remember(self, response, request, identity):
        """Remember identity on response.

        Implements ``morepath.App.remember_identity``, which is called
        from user login code.

        Given an identity object, store it on the response, for
        instance as a cookie. Some policies may not do any storing but
        instead retransmit authentication information each time in the
        request.

        :param response: response object on which to store identity.
        :type response: :class:`morepath.Response`
        :param request: request object.
        :type request: :class:`morepath.Request`
        :param identity: identity to remember.
        :type identity: :class:`morepath.Identity`

        """

    @abc.abstractmethod
    def forget(self, response, request):
        """Forget identity on response.

        Implements ``morepath.App.forget_identity``, which is called from
        user logout code.

        Remove identifying information from the response. This could
        delete a cookie or issue a basic auth re-authentication.

        :param response: response object on which to forget identity.
        :type response: :class:`morepath.Response`
        :param request: request object.
        :type request: :class:`morepath.Request`

        """
