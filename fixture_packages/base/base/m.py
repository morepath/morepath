import morepath

app = morepath.App()

class Foo(object):
    pass

@app.model(path='foo', model=Foo)
def get_foo():
    return Foo()
