import morepath


class Outer_app(morepath.App):
    pass


class App(morepath.App):
    pass


@Outer_app.mount("inner", App)
def inner_context():
    return App()


App.path(path="")


class Root:
    pass


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
