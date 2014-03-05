from morepath.autosetup import morepath_packages, autoconfig, autosetup
from base.m import app
import morepath


def setup_module(module):
    morepath.disable_implicit()


def test_import():
    import base
    import sub
    from ns import real
    from ns import real2
    assert sorted(list(morepath_packages()),
                  key=lambda module: module.__name__) == [
        base, real, real2, sub]


def test_autoconfig():
    c = autoconfig()
    c.commit()
    # a way to check whether model in base was registered, could
    # we make this a bit less low-level?
    assert app.traject.consume(['foo']) is not None


def test_autosetup():
    autosetup()
    # a way to check whether model in base was registered, could
    # we make this a bit less low-level?
    assert app.traject.consume(['foo']) is not None
