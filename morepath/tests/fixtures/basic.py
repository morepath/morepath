import morepath

app = morepath.App()


class Blah(object):
    pass

#@app.path(path='/')
class Root(object):
    def __init__(self):
        self.value = 'ROOT'

    @app.path(model=Blah, path='blah')
    def blah():
        return Blah()

@app.view(model=Blah)
def blah_default(self, request):
    return "Blah"

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


@app.view(model=Model, name='json', render=morepath.render_json)
def json(self, request):
    return {'id': self.id}


@app.view(model=Root)
def root_default(self, request):
    return "The root: %s" % self.value


@app.view(model=Root, name='link')
def root_link(self, request):
    return request.link(self)
