import importscan
import dectate
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
    importscan.scan(template)
    dectate.commit(template.App)

    c = Client(template.App())

    response = c.get('/world')
    assert response.body == b'<p>Hello world!</p>\n'


def test_template_override_fixture():
    importscan.scan(template_override)
    dectate.commit(template_override.App, template_override.SubApp)
    c = Client(template_override.App())

    response = c.get('/world')
    assert response.body == b'<p>Hello world!</p>\n'

    c = Client(template_override.SubApp())

    response = c.get('/world')
    assert response.body == b'<div>Hi world!</div>'


def test_template_override_not_directed():
    importscan.scan(template_override_under)
    with pytest.raises(ConfigError):
        dectate.commit(template_override_under.App,
                       template_override_under.SubApp)


def test_template_override_implicit_fixture():
    importscan.scan(template_override_implicit)
    dectate.commit(template_override_implicit.App,
                   template_override_implicit.SubApp)
    c = Client(template_override_implicit.App())

    response = c.get('/world')
    assert response.body == b'<p>Hello world!</p>\n'

    c = Client(template_override_implicit.SubApp())

    response = c.get('/world')
    assert response.body == b'<div>Hi world!</div>'


def test_unknown_extension_no_loader():
    importscan.scan(template_unknown_extension)
    with pytest.raises(ConfigError):
        dectate.commit(template_unknown_extension.App)


def test_unknown_extension_no_render():
    importscan.scan(template_unknown_extension_no_render)
    with pytest.raises(ConfigError):
        dectate.commit(template_unknown_extension_no_render.App)


def test_no_template_directories():
    importscan.scan(template_no_template_directories)
    # we accept no template directories, as it is possible
    # for a base frameworky app not to define any (ChameleonApp, Jinja2App)
    dectate.commit(template_no_template_directories.App)
