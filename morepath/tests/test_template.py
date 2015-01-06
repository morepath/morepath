import morepath
from webtest import TestApp as Client
import pytest
from .fixtures import template


def setup_module(module):
    morepath.disable_implicit()


def test_template():
    config = morepath.setup()
    config.scan(template)
    config.commit()
    c = Client(template.App())

    response = c.get('/world')
    assert response.body == b'<p>Hello world!</p>\n'

# def test_template():
#     config = morepath.setup()

#     class App(morepath.App):
#         testing_config = config

#     @App.path(path='{name}')
#     class Person(object):
#         def __init__(self, name):
#             self.name = name

#     @App.template_engine(extension='.format')
#     def get_format_render(path, original_render, settings):
#         with open(path, 'rb') as f:
#             template = f.read()
#         def render(content, request):
#             return template.format(**content)
#         return render

#     @App.html(model=Person, template='templates/person.format')
#     def person_default(self, request):
#         return { 'name': self.name }

#     config.commit()

#     c = Client(App())

#     response = c.get('/world')
#     assert response.body == b'<p>Hello world!</p>'
