import morepath


class App(morepath.App):
    pass


@App.path(path="/")
class Root:
    def __init__(self):
        self.value = "ROOT"


class Model:
    def __init__(self, id):
        self.id = id


@App.path(model=Model, path="{id}")
def get_model(id):
    return Model(id)


@App.view(model=Model)
def default(self, request):
    return "The view for model: %s" % self.id


@App.view(model=Model, name="link")
def link(self, request):
    return request.link(self)


@App.view(model=Model, name="json", render=morepath.render_json)
def json(self, request):
    return {"id": self.id}


@App.view(model=Root)
def root_default(self, request):
    return "The root: %s" % self.value


@App.view(model=Root, name="link")
def root_link(self, request):
    return request.link(self)
