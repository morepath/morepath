from comparch import Registry
from morepath.configure import register_resource
from morepath.interfaces import ResourceError, ResolveError
from morepath.publish import Publisher
from morepath.request import Request
from werkzeug.test import EnvironBuilder
import py.test

def get_request(*args, **kw):
    return Request(EnvironBuilder(*args, **kw).get_environ())

class Model(object):
    pass

def test_resource():
    reg = Registry()
    def resource(request, model):
        return "Resource!"
    
    register_resource(reg, Model, resource, name='')

    model = Model()
    publisher = Publisher(reg)
    result = publisher.publish(get_request(path=''), model)
    assert result == 'Resource!'

    
def test_predicates():
    reg = Registry()
    def resource(request, model):
        return "all"
    def post_resource(request, model):
        return "post"
    register_resource(reg, Model, resource, name='')
    register_resource(reg, Model, post_resource, name='', request_method='POST')
    
    model = Model()
    publisher = Publisher(reg)
    assert publisher.publish(get_request(path=''), model) == 'all'
    assert (publisher.publish(get_request(path='', method='POST'), model) ==
            'post')
    
def test_notfound():
    reg = Registry()
    model = Model()
    publisher = Publisher(reg)
    with py.test.raises(ResourceError):
        publisher.publish(get_request(path=''), model)
        
def test_notfound_with_predicates():
    reg = Registry()
    def resource(request, model):
        return "resource"
    register_resource(reg, Model, resource, name='')
    
    model = Model()
    publisher = Publisher(reg)
    with py.test.raises(ResolveError):
        publisher.publish(get_request(path='foo'), model)
   
