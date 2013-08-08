import morepath

app = morepath.App('myapp')

@app.root()
class App(object):
    pass

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


