import morepath


app = morepath.App()


@app.path(path='')
class Root(object):
    pass


@app.html(model=Root)
def index(self, request):
    return "the root"
