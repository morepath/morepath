import morepath
    
app = morepath.App()

@app.root()
class Root(object):
    def __init__(self):
        self.value = 'ROOT'

class Model(object):
    def __init__(self, id):
        self.id = id

@app.model(model=Model, path='{id}',
           variables=lambda model: { 'id': model.id })
def get_model(id):
    return Model(id)

@app.resource(model=Model)
def default(request, model):
    return "The resource for model: %s" % model.id

@app.resource(model=Model, name='link')
def link(request, model):
    return request.link(model)

@app.resource(model=Model, name='json', renderer=morepath.json_renderer)
def json(request, model):
    return {'id': model.id}

@app.resource(model=Root)
def root_default(request, model):
    return "The root: %s" % model.value

@app.resource(model=Root, name='link')
def root_link(request, model):
    return request.link(model)
