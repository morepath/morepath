import morepath
import os

class App(morepath.App):
    pass


@App.path(path='{name}')
class Person(object):
    def __init__(self, name):
        self.name = name


@App.template_engine(extension='.format')
def get_format_render(name, original_render, registry, search_path):
    def render(content, request):
        path = morepath.template_path(name, lookup=request.lookup)
        if path is None:
            path = os.path.join(search_path, name)
        with open(path, 'rb') as f:
            found_template = f.read().format
        return original_render(found_template(**content), request)
    return render


@App.template_path('templates/person.format')
def get_template_path():
    return 'templates/person.format'


@App.html(model=Person, template='templates/person.format')
def person_default(self, request):
    return { 'name': self.name }


class SubApp(App):
    pass


@SubApp.template_path('templates/person.format')
def get_template_path():
    return 'templates/person2.format'
