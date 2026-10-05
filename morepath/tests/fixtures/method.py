import morepath


class App(morepath.App):
    pass


class StaticMethod:
    pass


class Root:
    def __init__(self):
        self.value = "ROOT"

    @staticmethod
    @App.path(model=StaticMethod, path="static")
    def static_method():
        return StaticMethod()


@App.view(model=StaticMethod)
def static_method_default(self, request):
    return "Static Method"
