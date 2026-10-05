import morepath


class App(morepath.App):
    pass


# for which there is no known converter
class Dummy:
    pass


class Foo:
    pass


@App.path(path="/", model=Foo)
def get_foo(a=Dummy()):
    pass
