import pytest
import dectate
import morepath
from dectate import DirectiveReportError, ConflictError
from .fixtures import conflicterror
from morepath.compat import text_type


def test_missing_arguments_in_path_function_error():
    class App(morepath.App):
        pass

    class Model(object):
        pass

    @App.path(path='{id}', model=Model)
    def get_model():
        return Model()

    with pytest.raises(DirectiveReportError):
        dectate.commit(App)


def test_path_function_with_args_error():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @App.path(path='{id}', model=Model)
    def get_model(*args):
        return Model(args[0])

    with pytest.raises(DirectiveReportError):
        dectate.commit(App)


def test_path_function_with_kwargs():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @App.path(path='{id}', model=Model)
    def get_model(**kw):
        return Model(kw['id'])

    with pytest.raises(DirectiveReportError):
        dectate.commit(App)


def test_conflict_error_should_report_line_numbers():
    with pytest.raises(ConflictError) as e:
        dectate.commit(conflicterror.App)
    v = text_type(e.value)
    assert 'line 8' in v
    assert 'line 15' in v
