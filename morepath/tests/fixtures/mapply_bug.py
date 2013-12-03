import morepath


app = morepath.App()


@app.root()
class Root(object):
    pass


@app.html(model=Root)
def index(request, model):
    return "the root"
