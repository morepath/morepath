import morepath


class app(morepath.App):
    pass


class StaticMethod(object):
    pass


class Root(object):
    def __init__(self):
        self.value = 'ROOT'

    @staticmethod
    @app.path(model=StaticMethod, path='static')
    def static_method():
        return StaticMethod()


@app.view(model=StaticMethod)
def static_method_default(self, request):
    return "Static Method"
