from .interfaces import IResource, ILink
from werkzeug.wrappers import BaseRequest, BaseResponse


class Request(BaseRequest):
    def __init__(self, environ, populate_request=True, shallow=False):
        super(Request, self).__init__(environ, populate_request, shallow)
        self._resolver_info = None

    def set_resolver_info(self, info):
        self._resolver_info = info

    def resolver_info(self):
        return self._resolver_info

    def render(self, model, default=None):
        return IResource.adapt(
            self, model, lookup=self.lookup, default=default)
    
    # XXX add way to easily generate URL parameters too
    # XXX add way to determine application lookup context, or just
    # modify in request?
    def link(self, model, name=''):
        result = ILink.adapt(
            self, model, lookup=self.lookup)
        if name:
            result += '/' + name
        return result


class Response(BaseResponse):
    pass
