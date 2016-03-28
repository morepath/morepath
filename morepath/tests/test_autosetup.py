from collections import namedtuple
from morepath.autosetup import (
    morepath_packages, autoconfig, autosetup, import_package)
from base.m import App
from under_score.m import UnderscoreApp
import morepath
import pytest


def setup_module(module):
    morepath.disable_implicit()


def test_import():
    import base
    import sub
    import entrypoint
    from ns import real
    from ns import real2
    import under_score

    assert sorted(list(morepath_packages()),
                  key=lambda module: module.__name__) == [
                      base, entrypoint, real, real2, sub, under_score]


def test_autoconfig():
    c = autoconfig()
    c.commit()
    # a way to check whether model in base was registered, could
    # we make this a bit less low-level?
    assert App.config.registry.traject.consume(['foo']) is not None
    assert UnderscoreApp.config.registry.traject.consume(['foo']) is not None


def test_autosetup():
    autosetup()
    # a way to check whether model in base was registered, could
    # we make this a bit less low-level?
    assert App.config.registry.traject.consume(['foo']) is not None


def test_load_distribution():

    Distribution = namedtuple('Distribution', ['project_name'])

    assert import_package(Distribution('base')).m.App is App

    with pytest.raises(morepath.error.AutoImportError):
        import_package(Distribution('inexistant-package'))
