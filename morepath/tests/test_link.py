from reg import Lookup
from morepath.app import global_app
from morepath.interfaces import IRoot
#from morepath.interfaces import IRoot, IPath
from morepath import generic
from morepath.request import Request
from morepath.setup import root_path, setup
from werkzeug.test import EnvironBuilder


def get_request(*args, **kw):
    return Request(EnvironBuilder(*args, **kw).get_environ())


class Root(IRoot):
    pass


def test_root_path():
    setup()
    request = get_request()
    request.lookup = lookup = Lookup(global_app)
    root = Root()
    assert generic.path.component(request, root, lookup=lookup) is root_path
    assert generic.path(request, root, lookup=lookup) == ''
