import morepath

app = morepath.App()


@app.path(path='/')
class Root(object):
    def __init__(self):
        self.value = 'ROOT'


class Model(object):
    def __init__(self, id):
        self.id = id


@app.path(model=Model, path='{id}')
def get_model(id):
    return Model(id)


@app.view(model=Model)
def default(request, model):
    return "The view for model: %s" % model.id


@app.view(model=Model, name='link')
def link(request, model):
    return request.link(model)


@app.view(model=Model, name='json', render=morepath.render_json)
def json(request, model):
    return {'id': model.id}


@app.view(model=Root)
def root_default(request, model):
    return "The root: %s" % model.value


@app.view(model=Root, name='link')
def root_link(request, model):
    return request.link(model)
