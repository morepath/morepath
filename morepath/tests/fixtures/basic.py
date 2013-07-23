from morepath import app, model, resource

class App(object):
    pass

@app(model=App, name='myapp')
def get_app():
    return App()

class Model(object):
    def __init__(self, id):
        self.id = id

@model(base=App, model=Model,
       path='{id}',
       variables=lambda model: { 'id': model.id })
def get_model(id):
    return Model(id)

@resource(model=Model)
def default(request, model):
    return "The resource for model: %s" % model.id


