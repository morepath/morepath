import morepath

outer_app = morepath.App('outer')
app = morepath.App('inner')


@outer_app.mount('inner', app)
def inner_context():
    return {}


@app.path(path='')
class Root(object):
    pass


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
