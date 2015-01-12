import morepath


class App(morepath.App):
    pass


@App.path(path='{name}')
class Person(object):
    def __init__(self, name):
        self.name = name


@App.html(model=Person, template='person.unknown')
def person_default(self, request):
    return {'name': self.name}
