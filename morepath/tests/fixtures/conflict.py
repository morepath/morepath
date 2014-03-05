import morepath

app = morepath.App()


@app.path(path='/')
class Root(object):
    pass


@app.path(path='/', model=Root)
def get_root():
    return Root()
