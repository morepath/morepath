from reg import Lookup
from morepath.app import App
from morepath.publish import publish
from morepath.request import Request, Response
from morepath.resource import register_resource, render_json
from morepath.setup import setup
from werkzeug.test import EnvironBuilder


def get_request(*args, **kw):
    app = kw.pop('app')
    lookup = Lookup(app.class_lookup())
    result = Request(EnvironBuilder(*args, **kw).get_environ())
    result.lookup = lookup
    return result


class Model(object):
    pass


# XXX these tests have gained more dependencies, on app and setup and
# lookup generation. see about refactor code so that they can be tested
# with less heavy installation
def test_resource():
    setup()
    app = App()

    def resource(request, model):
        return "Resource!"

    register_resource(app, Model, resource, predicates=dict(name=''))

    model = Model()
    result = publish(get_request(path='', app=app), model)
    assert result.data == 'Resource!'


def test_predicates():
    setup()
    app = App()

    def resource(request, model):
        return "all"

    def post_resource(request, model):
        return "post"

    register_resource(app, Model, resource, predicates=dict(name=''))
    register_resource(app, Model, post_resource,
                      predicates=dict(name='', request_method='POST'))

    model = Model()
    assert publish(get_request(path='', app=app), model).data == 'all'
    assert (publish(get_request(path='', method='POST', app=app),
                    model).data == 'post')


def test_notfound():
    setup()
    app = App()
    model = Model()
    response = publish(get_request(path='', app=app), model)
    assert response.status == '404 NOT FOUND'


def test_notfound_with_predicates():
    setup()
    app = App()

    def resource(request, model):
        return "resource"

    register_resource(app, Model, resource, predicates=dict(name=''))
    model = Model()
    response = publish(get_request(path='foo', app=app), model)
    assert response.status == '404 NOT FOUND'


def test_response_returned():
    setup()
    app = App()

    def resource(request, model):
        return Response('Hello world!')

    register_resource(app, Model, resource)
    model = Model()
    response = publish(get_request(path='', app=app), model)
    assert response.data == 'Hello world!'


def test_render():
    setup()
    app = App()

    def resource(request, model):
        return { 'hey': 'hey' }

    register_resource(app, Model, resource, render=render_json)
    
    request = get_request(path='', app=app)
    model = Model()
    response = publish(request, model)
    # when we get the response, the json will be rendered
    assert response.data == '{"hey": "hey"}'
    # but we get the original json out when we render
    assert request.render(model) == { 'hey': 'hey' }
    
# def test_model_is_response():
#     class MyModel(Response):
#         pass
#     reg = Registry()
#     model = MyModel()

#     assert publish(get_request(path=''), model, reg) is model

#     # if there is a name left, it cannot resolve to model
#     with py.test.raises(ResolveError):
#         publish(get_request(path='foo'), model, reg)

# def test_model_is_response_factory():
#     class MyResponse(Response):
#         pass

#     my_response = MyResponse()
#     class MyModel(IResponseFactory):
#         def __call__(self):
#             return my_response

#     reg = Registry()
#     model = MyModel()
#     assert publish(get_request(path=''), model, reg) is my_response

# def test_resource_as_response_factory():
#     reg = Registry()
#     model = Model()

#     class MyResponse(Response):
#         def __init__(self, request, context):
#             self.request = request
#             self.context = context

#     class MyResource(IResponseFactory):
#         def __init__(self, request, context):
#             self.request = request
#             self.context = context

#         def __call__(self):
#             return MyResponse(self.request, self.context)

#     reg.register(IResource, (Request, Model), MyResource)

#     req = get_request(path='')
#     response = publish(req, model, reg)
#     assert response.request is req
#     assert response.context is model

# XXX add tests for renderer
