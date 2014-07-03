import morepath


class app(morepath.App):
    pass


class Model(object):
    def __init__(self, id):
        self.id = id


@app.path(model=Model, path='{id}')
def get_model(id):
    return Model(id)


with app.view(model=Model) as view:
    @view()
    def default(self, request):
        return "Default view: %s" % self.id

    @view(name='edit')
    def edit(self, request):
        return "Edit view: %s" % self.id
