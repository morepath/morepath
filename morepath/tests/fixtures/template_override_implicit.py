import morepath
from .template_engine import FormatLoader


class App(morepath.App):
    pass


@App.path(path='{name}')
class Person(object):
    def __init__(self, name):
        self.name = name


@App.template_directory()
def get_template_directory():
    return 'templates'


@App.template_loader(extension='.format')
def get_template_loader(template_directories, settings):
    return FormatLoader(template_directories)


@App.template_render(extension='.format')
def get_format_render(loader, name, original_render):
    template = loader.get(name)

    def render(content, request):
        return original_render(template.render(**content), request)
    return render


@App.html(model=Person, template='person.format')
def person_default(self, request):
    return {'name': self.name}


class SubApp(App):
    pass


@SubApp.template_directory()
def get_template_directory_override():
    return 'templates2'
