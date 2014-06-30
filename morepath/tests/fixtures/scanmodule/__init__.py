from .theapp import app


@app.path(path='/')
class Root(object):
    def __init__(self):
        self.value = 'ROOT'


@app.view(model=Root)
def root_default(self, request):
    return "The root: %s" % self.value
