import morepath


class app(morepath.App):
    pass


# for which there is no known converter
class Dummy:
    pass


class Foo:
    pass


@app.path(path="/", model=Foo)
def get_foo(a=Dummy()):
    pass
