from morepath import generic
from werkzeug.wrappers import (BaseRequest, BaseResponse,
                               CommonResponseDescriptorsMixin)
from werkzeug.utils import cached_property


class Request(BaseRequest):
    def __init__(self, environ, populate_request=True, shallow=False):
        super(Request, self).__init__(environ, populate_request, shallow)
        self._resolver_info = None
        self.unconsumed = []
        self.mounts = []

    @cached_property
    def identity(self):
        # XXX annoying circular dependency
        from .security import NO_IDENTITY
        return generic.identify(self, lookup=self.lookup,
                                default=NO_IDENTITY)

    def set_resolver_info(self, info):
        self._resolver_info = info

    def resolver_info(self):
        return self._resolver_info

    # XXX how to make view in other application context?
    def view(self, model, default=None):
        return generic.view(
            self, model, lookup=self.lookup, default=default)

    # XXX add way to easily generate URL parameters too
    # XXX add way to determine application lookup context, or just
    # modify in request?
    def link(self, model, name=''):
        result = generic.link(
            self, model, lookup=self.lookup)
        if name:
            result += '/' + name
        return result


class Response(BaseResponse, CommonResponseDescriptorsMixin):
    pass
