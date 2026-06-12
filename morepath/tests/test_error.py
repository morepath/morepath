from __future__ import annotations

import pytest

import dectate
import morepath
from dectate import ConflictError, DirectiveReportError

from .fixtures import conflicterror


def test_missing_arguments_in_path_function_error() -> None:
    class App(morepath.App):
        pass

    class Model:
        pass

    @App.path(path="{id}", model=Model)
    def get_model() -> Model:
        return Model()

    with pytest.raises(DirectiveReportError):
        dectate.commit(App)


def test_path_function_with_args_error() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @App.path(path="{id}", model=Model)
    def get_model(*args: str) -> Model:
        return Model(args[0])

    with pytest.raises(DirectiveReportError):
        dectate.commit(App)


def test_path_function_with_kwargs() -> None:
    class App(morepath.App):
        pass

    class Model:
        def __init__(self, id: str) -> None:
            self.id = id

    @App.path(path="{id}", model=Model)
    def get_model(**kw: str) -> Model:
        return Model(kw["id"])

    with pytest.raises(DirectiveReportError):
        dectate.commit(App)


def test_conflict_error_should_report_line_numbers() -> None:
    with pytest.raises(ConflictError) as e:
        dectate.commit(conflicterror.App)
    v = str(e.value)
    assert "line 8" in v
    assert "line 13" in v
