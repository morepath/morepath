import morepath


class app(morepath.App):
    pass


class StaticMethod(object):
    pass


class ClassMethod(object):
    def __init__(self, cls):
        self.cls = cls


class Root(object):
    def __init__(self):
        self.value = 'ROOT'

    @app.path(model=StaticMethod, path='static')
    @staticmethod
    def static_method():
        return StaticMethod()

    @app.path(model=ClassMethod, path='class')
    @classmethod
    def class_method(cls):
        assert cls is Root
        return ClassMethod(cls)


@app.view(model=StaticMethod)
def static_method_default(self, request):
    return "Static Method"


@app.view(model=ClassMethod)
def class_method_default(self, request):
    assert self.cls is Root
    return "Class Method"
