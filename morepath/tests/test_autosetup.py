from collections import namedtuple
from morepath.autosetup import (
    morepath_packages, import_package)
from base.m import App
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


def test_load_distribution():

    Distribution = namedtuple('Distribution', ['project_name'])

    assert import_package(Distribution('base')).m.App is App

    with pytest.raises(morepath.error.AutoImportError):
        import_package(Distribution('inexistant-package'))
