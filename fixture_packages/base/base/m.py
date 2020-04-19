import morepath


class App(morepath.App):
    pass


class Foo:
    pass


@App.path(path="foo", model=Foo)
def get_foo():
    return Foo()
