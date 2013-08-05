from .fixtures import basic
from comparch import Registry, Lookup
from comparch import ChainClassLookup
from morepath.directive import Config
from morepath.link import path
from morepath.publish import Publisher
from morepath.interfaces import IRoot, IConsumer
from morepath.request import Request
from werkzeug.test import EnvironBuilder
from morepath.traject import TrajectConsumer

def get_request(*args, **kw):
    return Request(EnvironBuilder(*args, **kw).get_environ())

class Root(IRoot):
    pass

def test_basic():
    config = Config()
    config.scan(basic)
    config.commit()

    global_registry = Registry()

    lookup = Lookup(ChainClassLookup(basic.reg, global_registry))

    # XXX find a better place to do this, with a directive or something
    global_registry.register(IConsumer, (object,),
                             TrajectConsumer(lookup)) 
        
    publisher = Publisher(lookup)

    root = Root()
    
    request = get_request('myapp/something')
    request.lookup = lookup # XXX need to have a better place to place this
    result = publisher.publish(request, root)
    assert result == 'The resource for model: something'

    m = basic.Model('foo')
    assert request.link(m) == '/myapp/foo'
