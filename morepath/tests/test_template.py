import os
import morepath
from morepath.error import ConfigError
from webtest import TestApp as Client
import pytest
from .fixtures import (
    template, template_override, template_override_implicit,
    template_unknown_extension, template_unknown_extension_no_render,
    template_no_template_directories, template_override_under)


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


def test_template_override_not_directed():
    config = morepath.setup()
    config.scan(template_override_under)
    with pytest.raises(ConfigError):
        config.commit()


def test_template_override_implicit_fixture():
    config = morepath.setup()
    config.scan(template_override_implicit)
    config.commit()
    c = Client(template_override_implicit.App())

    response = c.get('/world')
    assert response.body == b'<p>Hello world!</p>\n'

    c = Client(template_override_implicit.SubApp())

    response = c.get('/world')
    assert response.body == b'<div>Hi world!</div>'


def test_unknown_extension_no_loader():
    config = morepath.setup()
    config.scan(template_unknown_extension)
    with pytest.raises(ConfigError):
        config.commit()



def test_unknown_extension_no_render():
    config = morepath.setup()
    config.scan(template_unknown_extension_no_render)
    with pytest.raises(ConfigError):
        config.commit()


def test_no_template_directories():
    config = morepath.setup()
    config.scan(template_no_template_directories)
    with pytest.raises(ConfigError):
        config.commit()
