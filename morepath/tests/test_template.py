from morepath.error import ConfigError
from webtest import TestApp as Client
import pytest
from .fixtures import (
    template, template_override, template_override_implicit,
    template_unknown_extension, template_unknown_extension_no_render,
    template_no_template_directories, template_override_under)


def test_template_fixture():
    c = Client(template.App())

    response = c.get('/world')
    assert response.body == b'<p>Hello world!</p>\n'


def test_template_override_fixture():
    c = Client(template_override.App())

    response = c.get('/world')
    assert response.body == b'<p>Hello world!</p>\n'

    c = Client(template_override.SubApp())

    response = c.get('/world')
    assert response.body == b'<div>Hi world!</div>'


def test_template_override_not_directed():
    with pytest.raises(ConfigError):
        template_override_under.SubApp.commit()


def test_template_override_implicit_fixture():
    c = Client(template_override_implicit.App())

    response = c.get('/world')
    assert response.body == b'<p>Hello world!</p>\n'

    c = Client(template_override_implicit.SubApp())

    response = c.get('/world')
    assert response.body == b'<div>Hi world!</div>'


def test_unknown_extension_no_loader():
    with pytest.raises(ConfigError):
        template_unknown_extension.App.commit()


def test_unknown_extension_no_render():
    with pytest.raises(ConfigError):
        template_unknown_extension_no_render.App.commit()


def test_no_template_directories():
    # we accept no template directories, as it is possible
    # for a base frameworky app not to define any (ChameleonApp, Jinja2App)
    assert template_no_template_directories.App.commit() == \
        {template_no_template_directories.App}
