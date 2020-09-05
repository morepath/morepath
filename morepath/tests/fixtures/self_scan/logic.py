from .app import App


@App.path(path="/")
class Root:
    def __init__(self):
        self.value = "ROOT"


class Model:
    def __init__(self, id):
        self.id = id


@App.view(model=Root)
def root_default(self, request):
    return "The root: %s" % self.value
