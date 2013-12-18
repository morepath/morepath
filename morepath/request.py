from morepath import generic
from werkzeug.wrappers import (BaseRequest, BaseResponse,
                               CommonResponseDescriptorsMixin)
from werkzeug.utils import cached_property
from .traject import parse_path


class Request(BaseRequest):
    """Request.

    Extends :class:`werkzeug.wrappers.BaseRequest`
    """
    def __init__(self, environ, populate_request=True, shallow=False):
        super(Request, self).__init__(environ, populate_request, shallow)
        self.unconsumed = parse_path(self.path)
        self.mounts = []

    @cached_property
    def identity(self):
        """Self-proclaimed identity of the user.

        The identity is established using the identity policy. Normally
        this would be an instance of :class:`morepath.security.Identity`.

        If no identity is claimed or established, the identity will be
        the special value :attr:`morepath.security.NO_IDENTITY`.

        The identity can be used for authentication/authorization of
        the user, using Morepath permission directives.
        """
        # XXX annoying circular dependency
        from .security import NO_IDENTITY
        return generic.identify(self, lookup=self.lookup,
                                default=NO_IDENTITY)

    # XXX how to make view in other application context?
    def view(self, model, default=None, **predicates):
        """Call view for model.

        This does not render the view, but calls the appropriate
        view function and returns its result.

        :param model: the model to call the view on.
        :param default: default value if view is not found.
        :param predicates: extra predicates to modify view
          lookup, such as ``name`` and ``request_method``. The default
          ``name`` is empty, so the default view is looked up,
          and the default ``request_method`` is ``GET``. If you introduce
          your own predicates you can specify your own default.
        """
        view = generic.view.component(
            self, model, lookup=self.lookup, default=default,
            predicates=predicates)
        if view is None:
            return None
        return view(self, model)

    # XXX add way to easily generate URL parameters too
    # XXX how to make link work in other application context?
    def link(self, model, name=''):
        """Create a link (URL) to a view on a model.

        :param model: the model to link to.
        :param name: the name of the view to link to. If omitted, the
          the default view is looked up.
        """
        result = generic.link(
            self, model, lookup=self.lookup)
        if name:
            result += '/' + name
        return result


class Response(BaseResponse, CommonResponseDescriptorsMixin):
    """Response.

    Extends :class:`werkzeug.wrappers.BaseResponse` and
    :class:`werkzeug.wrappers.CommonResponseDescriptorsMixin`.
    """
