import morepath


class outer_app(morepath.App):
    pass


class app(morepath.App):
    pass


@outer_app.mount('inner', app)
def inner_context():
    return app()


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
def default(self, request):
    return "The view for model: %s" % self.id


@app.view(model=Model, name='link')
def link(self, request):
    return request.link(self)
