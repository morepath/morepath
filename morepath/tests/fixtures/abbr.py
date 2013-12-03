import morepath

app = morepath.App()


class Model(object):
    def __init__(self, id):
        self.id = id


@app.model(model=Model, path='{id}',
           variables=lambda model: {'id': model.id})
def get_model(id):
    return Model(id)


with app.view(model=Model) as view:
    @view()
    def default(request, model):
        return "Default view: %s" % model.id

    @view(name='edit')
    def edit(request, model):
        return "Edit view: %s" % model.id
