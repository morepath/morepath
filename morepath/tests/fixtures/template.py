import morepath


class App(morepath.App):
    pass


@App.path(path='{name}')
class Person(object):
    def __init__(self, name):
        self.name = name


@App.template_engine(extension='.format')
def get_format_render(path, original_render, settings):
    with open(path, 'rb') as f:
        template = f.read()
    def render(content, request):
        return original_render(template.format(**content), request)
    return render


@App.html(model=Person, template='templates/person.format')
def person_default(self, request):
    return { 'name': self.name }
