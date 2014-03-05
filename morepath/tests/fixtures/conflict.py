import morepath

app = morepath.App()


@app.path(path='/')
class Root(object):
    def __init__(self):
        self.value = 'ROOT'


@app.path(path='/', model=Root)
def get_root():
    return Root()
