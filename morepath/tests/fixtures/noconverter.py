import morepath


class app(morepath.App):
    pass


# for which there is no known converter
class Dummy(object):
    pass


class Foo(object):
    pass


@app.path(path='/', model=Foo)
def get_foo(a=Dummy()):
    pass
