import pytest
import morepath
from morepath.error import DirectiveReportError


def test_missing_arguments_in_path_function_error():
    config = morepath.setup()

    class App(morepath.App):
        testing_config = config

    class Model(object):
        pass

    @App.path(path='{id}', model=Model)
    def get_model():
        return Model()

    @App.view(model=Model)
    def model_get(self, request):
        return "Here"

    @App.view(model=Model, name='link')
    def model_link_get(self, request):
        return request.link(self)

    with pytest.raises(DirectiveReportError):
        config.commit()


def test_path_function_with_args_error():
    config = morepath.setup()

    class App(morepath.App):
        testing_config = config

    class Model(object):
        def __init__(self, id):
            self.id = id

    @App.path(path='{id}', model=Model)
    def get_model(*args):
        return Model(args[0])

    @App.view(model=Model)
    def model_get(self, request):
        return "Here"

    @App.view(model=Model, name='link')
    def model_link_get(self, request):
        return request.link(self)

    with pytest.raises(DirectiveReportError):
        config.commit()


def test_path_function_with_kwargs():
    config = morepath.setup()

    class App(morepath.App):
        testing_config = config

    class Model(object):
        def __init__(self, id):
            self.id = id

    @App.path(path='{id}', model=Model)
    def get_model(**kw):
        return Model(kw['id'])

    @App.view(model=Model)
    def model_get(self, request):
        return "Here"

    @App.view(model=Model, name='link')
    def model_link_get(self, request):
        return request.link(self)

    with pytest.raises(DirectiveReportError):
        config.commit()
