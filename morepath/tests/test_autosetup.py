from collections import namedtuple

import pytest
from base.m import App

import morepath
from morepath.autosetup import (
    DependencyMap,
    autoscan,
    caller_module,
    caller_package,
    import_package,
    morepath_packages,
)


def test_import():
    import base
    import entrypoint

    # Pacakges to be ignored
    import no_mp
    import no_mp_sub
    import sub
    import under_score
    from ns import nomp, real, real2

    found = set(morepath_packages())
    assert {base, entrypoint, real, real2, sub, under_score} <= found
    assert {no_mp, nomp, no_mp_sub}.isdisjoint(found)


def test_load_distribution():

    Distribution = namedtuple("Distribution", ["name"])

    assert import_package(Distribution("base")).m.App is App

    with pytest.raises(morepath.error.AutoImportError):
        import_package(Distribution("inexistant-package"))


def invoke(callable):
    "Add one frame to stack, no other purpose."
    return callable()


def test_caller_module():
    import sys

    assert caller_module(1) == sys.modules[__name__]
    assert invoke(caller_module) == sys.modules[__name__]


def test_caller_package():
    import sys

    assert caller_package(1) == sys.modules[__package__]
    assert invoke(caller_package) == sys.modules[__package__]


def test_autoscan(monkeypatch):
    import sys

    for k in "base.m", "entrypoint.app", "under_score.m":
        monkeypatch.delitem(sys.modules, k, raising=False)

    autoscan()

    assert "base.m" in sys.modules
    assert "entrypoint.app" in sys.modules
    assert "under_score.m" in sys.modules


def test_circular_dependency():
    m = DependencyMap()
    m._d = {
        "parent": {"grandparent"},
        "child-a": {"child-b", "parent"},
        "child-b": {"child-a", "parent"},
        "grandchild": {"child-a", "child-b"},
    }

    for node in ("grandchild", "child-a", "child-b", "parent"):
        assert m.depends(node, "grandparent")
