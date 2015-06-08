import morepath

app = morepath.App()

class Foo(object):
    pass

@app.path(path='bar', model=Foo)
def get_foo():
    return Foo()
