from .fixtures import basic
from comparch import Registry
from morepath.directive import Config
from morepath.link import path
from morepath.publish import Publisher
from morepath.interfaces import IRoot
from morepath.request import Request
from werkzeug.test import EnvironBuilder

def get_request(*args, **kw):
    return Request(EnvironBuilder(*args, **kw).get_environ())

class Root(IRoot):
    pass

def test_basic():
    reg = Registry()
    config = Config(reg)
    config.scan(basic)
    config.commit()

    publisher = Publisher(reg)

    root = Root()
    
    request = get_request('myapp/something')
    request.lookup = reg # XXX need to have a better place to place this
    result = publisher.publish(request, root)
    assert result == 'The resource for model: something'

    m = basic.Model('foo')
    assert request.link(m) == '/myapp/foo'
