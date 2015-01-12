import morepath
from .template_engine import FormatLoader


class App(morepath.App):
    pass


@App.path(path='{name}')
class Person(object):
    def __init__(self, name):
        self.name = name


@App.template_loader(extension='.unknown')
def get_template_loader(template_directories, settings):
    return FormatLoader(template_directories)


@App.template_directory()
def get_template_directory():
    return 'templates'


@App.html(model=Person, template='person.unknown')
def person_default(self, request):
    return {'name': self.name}
