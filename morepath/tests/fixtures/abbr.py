import morepath


class App(morepath.App):
    pass


class Model:
    def __init__(self, id):
        self.id = id


@App.path(model=Model, path="{id}")
def get_model(id):
    return Model(id)


with App.view(model=Model) as view:

    @view()
    def default(self, request):
        return "Default view: %s" % self.id

    @view(name="edit")
    def edit(self, request):
        return "Edit view: %s" % self.id
