from comparch import Registry
from morepath.interfaces import (IResource, IResponseFactory,
                                 ResourceError, ResolveError)
from morepath.publish import publish
from morepath.request import Request, Response
from morepath.resource import register_resource
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
    
    register_resource(reg, Model, resource, predicates=dict(name=''))

    model = Model()
    result = publish(get_request(path=''), model, reg)
    assert result.data == 'Resource!'

    
def test_predicates():
    reg = Registry()
    def resource(request, model):
        return "all"
    def post_resource(request, model):
        return "post"
    register_resource(reg, Model, resource, predicates=dict(name=''))
    register_resource(reg, Model, post_resource,
                      predicates=dict(name='', request_method='POST'))
    
    model = Model()
    assert publish(get_request(path=''), model, reg).data == 'all'
    assert (publish(get_request(path='', method='POST'), model, reg).data ==
            'post')
    
def test_notfound():
    reg = Registry()
    model = Model()
    with py.test.raises(ResourceError):
        publish(get_request(path=''), model, reg)
        
def test_notfound_with_predicates():
    reg = Registry()
    def resource(request, model):
        return "resource"
    register_resource(reg, Model, resource, predicates=dict(name=''))
    
    model = Model()
    with py.test.raises(ResolveError):
        publish(get_request(path='foo'), model, reg)
   
def test_model_is_response():
    class MyModel(Response):
        pass
    reg = Registry()
    model = MyModel()

    assert publish(get_request(path=''), model, reg) is model

    # if there is a name left, it cannot resolve to model
    with py.test.raises(ResolveError):
        publish(get_request(path='foo'), model, reg)

def test_model_is_response_factory():
    class MyResponse(Response):
        pass

    my_response = MyResponse()
    class MyModel(IResponseFactory):
        def __call__(self):
            return my_response

    reg = Registry()
    model = MyModel()
    assert publish(get_request(path=''), model, reg) is my_response

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
    response = publish(req, model, reg)
    assert response.request is req
    assert response.context is model

# XXX add tests for renderer
