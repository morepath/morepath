import morepath
import os


class App(morepath.App):
    pass


@App.path(path='{name}')
class Person(object):
    def __init__(self, name):
        self.name = name


@App.template_engine(extension='.format')
def get_format_render(path, original_render, registry, search_path):
    # this integration does not support template_file overrides, just
    # loads them right from the start
    with open(os.path.join(search_path, path), 'rb') as f:
        template = f.read()
    def render(content, request):
        return original_render(template.format(**content), request)
    return render


@App.html(model=Person, template='templates/person.format')
def person_default(self, request):
    return { 'name': self.name }
