from comparch import Registry
from morepath.resource import register_resource
from morepath.interfaces import (IResource, IResponseFactory,
                                 ResourceError, ResolveError)
from morepath.publish import publish
from morepath.request import Request, Response
from werkzeug.test import EnvironBuilder
import py.test

def get_request(*args, **kw):
    return Request(EnvironBuilder(*args, **kw).get_environ())

class Model(object):
    pass

def dummy_get_lookup(lookup, obj):
    return None

def test_resource():
    reg = Registry()
    def resource(request, model):
        return "Resource!"
    
    register_resource(reg, Model, resource, name='')

    model = Model()
    result = publish(get_request(path=''), model, reg, dummy_get_lookup)
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
    assert publish(get_request(path=''), model, reg, dummy_get_lookup) == 'all'
    assert (publish(get_request(path='', method='POST'), model, reg, dummy_get_lookup) ==
            'post')
    
def test_notfound():
    reg = Registry()
    model = Model()
    with py.test.raises(ResourceError):
        publish(get_request(path=''), model, reg, dummy_get_lookup)
        
def test_notfound_with_predicates():
    reg = Registry()
    def resource(request, model):
        return "resource"
    register_resource(reg, Model, resource, name='')
    
    model = Model()
    with py.test.raises(ResolveError):
        publish(get_request(path='foo'), model, reg, dummy_get_lookup)
   
def test_model_is_response():
    class MyModel(Response):
        pass
    reg = Registry()
    model = MyModel()

    assert publish(get_request(path=''), model, reg, dummy_get_lookup) is model

    # if there is a name left, it cannot resolve to model
    with py.test.raises(ResolveError):
        publish(get_request(path='foo'), model, reg, dummy_get_lookup)

def test_model_is_response_factory():
    class MyResponse(Response):
        pass

    my_response = MyResponse()
    class MyModel(IResponseFactory):
        def __call__(self):
            return my_response

    reg = Registry()
    model = MyModel()
    assert publish(get_request(path=''), model, reg, dummy_get_lookup) is my_response

def test_resource_as_response_factory():
    reg = Registry()
    model = Model()

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
    response = publish(req, model, reg, dummy_get_lookup)
    assert response.request is req
    assert response.context is model
