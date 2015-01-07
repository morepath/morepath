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
    template = None
    if not registry.has_template_file(name):
        with open(os.path.join(search_path, name), 'rb') as f:
            template = f.read().format
    def render(content, request):
        if template is None:
            path = registry.get_template_file(name, request)
            with open(path, 'rb') as f:
                found_template = f.read().format
        else:
            found_template = template
        return original_render(found_template(**content), request)
    return render


@App.template_file('templates/person.format')
def get_template(request):
    return 'templates/person.format'


@App.html(model=Person, template='templates/person.format')
def person_default(self, request):
    return { 'name': self.name }


class SubApp(App):
    pass


@SubApp.template_file('templates/person.format')
def get_template(request):
    return 'templates/person2.format'
