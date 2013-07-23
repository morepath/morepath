from comparch import Registry
from morepath.resource import register_resource
from morepath.interfaces import (IResource, IResponseFactory,
                                 ResourceError, ResolveError)
from morepath.publish import Publisher
from morepath.request import Request, Response
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
   
def test_model_is_response():
    class MyModel(Response):
        pass
    reg = Registry()
    model = MyModel()
    publisher = Publisher(reg)
    assert publisher.publish(get_request(path=''), model) is model

    # if there is a name left, it cannot resolve to model
    with py.test.raises(ResolveError):
        publisher.publish(get_request(path='foo'), model)

def test_model_is_response_factory():
    class MyResponse(Response):
        pass

    my_response = MyResponse()
    class MyModel(IResponseFactory):
        def __call__(self):
            return my_response

    reg = Registry()
    model = MyModel()
    publisher = Publisher(reg)
    assert publisher.publish(get_request(path=''), model) is my_response

def test_resource_as_response_factory():
    reg = Registry()
    model = Model()
    publisher = Publisher(reg)

    class MyResponse(Response):
        def __init__(self, request, context):
            self.request = request
            self.context = context
            
    class MyResource(IResponseFactory):
        def __init__(self, request, context):
            self.request = request
            self.context = context
            
        def __call__(self):
            return MyResponse(self.request, self.context)
        
    reg.register(IResource, (Request, Model), MyResource)

    req = get_request(path='')
    response = publisher.publish(req, model)
    assert response.request is req
    assert response.context is model
    
