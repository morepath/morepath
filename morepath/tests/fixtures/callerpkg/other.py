import morepath


class app(morepath.App):
    pass


@app.path(path='/')
class Root(object):
    pass


@app.view(model=Root)
def root_default(self, request):
    return "Hello world"
