import morepath


app = morepath.App()


@app.model(path='')
class Root(object):
    pass


@app.html(model=Root)
def index(request, model):
    return "the root"
