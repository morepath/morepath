import os
import morepath
from morepath.error import ConfigError
from webtest import TestApp as Client
import pytest
from .fixtures import template, template_override


def setup_module(module):
    morepath.disable_implicit()


def test_template_fixture():
    config = morepath.setup()
    config.scan(template)
    config.commit()
    c = Client(template.App())

    response = c.get('/world')
    assert response.body == b'<p>Hello world!</p>\n'


def test_template_override_fixture():
    config = morepath.setup()
    config.scan(template_override)
    config.commit()
    c = Client(template_override.App())

    response = c.get('/world')
    assert response.body == b'<p>Hello world!</p>\n'

    c = Client(template_override.SubApp())

    response = c.get('/world')
    assert response.body == b'<div>Hi world!</div>'
