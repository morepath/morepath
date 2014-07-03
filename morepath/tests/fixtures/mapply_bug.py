import morepath


class app(morepath.App):
    pass


@app.path(path='')
class Root(object):
    pass


@app.html(model=Root)
def index(self, request):
    return "the root"
