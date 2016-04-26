import morepath


class App(morepath.App):
    pass


@App.path(path='')
class Root(object):
    pass


@App.view(model=Root)
def hello_world(self, request):
    return "Hello world!"


if __name__ == '__main__':
    morepath.run(App())
