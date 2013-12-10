from morepath.autosetup import morepath_packages, autoconfig, autosetup
from base.m import app, get_foo


def test_import():
    import base
    import sub
    from ns import real
    assert sorted(list(morepath_packages()),
                  key=lambda module: module.__name__) == [base, real, sub]


def test_autoconfig():
    c = autoconfig()
    c.commit()
    # a way to check whether model in base was registered, could
    # we make this a bit less low-level?
    assert app.traject(['foo']) == (get_foo, [], {})


def test_autosetup():
    autosetup()
    # a way to check whether model in base was registered, could
    # we make this a bit less low-level?
    assert app.traject(['foo']) == (get_foo, [], {})
