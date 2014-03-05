import morepath


app = morepath.App()


@app.path(path='/')
class Root(object):
    pass


@app.view(model=Root)
def root_default(self, request):
    return "Hello world"
