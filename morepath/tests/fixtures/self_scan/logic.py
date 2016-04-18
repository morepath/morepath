from .app import App


@App.path(path='/')
class Root(object):
    def __init__(self):
        self.value = 'ROOT'


class Model(object):
    def __init__(self, id):
        self.id = id


@App.view(model=Root)
def root_default(self, request):
    return "The root: %s" % self.value
