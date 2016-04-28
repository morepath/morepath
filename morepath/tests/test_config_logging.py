import logging
import morepath
from webtest import TestApp as Client

from .fixtures import basic
from .capturelog import CaptureLog


def test_config_logging_implicit_commit():
    class App(morepath.App):
        pass

    @App.path(path='')
    class Model(object):
        pass

    @App.view(model=Model)
    def default(self, request):
        return "View"

    with CaptureLog('morepath.directive.path', logging.DEBUG) as captured:
        c = Client(App())
        response = c.get('/')
        assert response.body == b'View'

        messages = [record.getMessage() for record in captured.records]
        assert messages == [
            "@morepath.tests.test_config_logging.App.path(path='') on {!r}"
            .format(Model)]

    # Instantiating and serving a second app does not trigger a new
    # commit:
    with CaptureLog('morepath.directive.path', logging.DEBUG) as captured:
        c = Client(App())
        response = c.get('/')
        assert response.body == b'View'
        messages = [record.getMessage() for record in captured.records]
        assert messages == []


def test_config_logging_explicit_commit():
    # Manually commit the app:
    with CaptureLog('morepath.directive.path', logging.DEBUG) as captured:
        assert basic.app.commit() == {basic.app}

    messages = [record.getMessage() for record in captured.records]
    messages.sort()

    assert messages == [
        "@morepath.tests.fixtures.basic.app.path("
        "model=<class 'morepath.tests.fixtures.basic.Model'>, "
        "path='{id}') on morepath.tests.fixtures.basic.get_model",
        "@morepath.tests.fixtures.basic.app.path(path='/') on "
        "<class 'morepath.tests.fixtures.basic.Root'>"
    ]

    with CaptureLog('morepath.directive.path', logging.DEBUG) as captured:
        c = Client(basic.app())
        response = c.get('/')
        assert response.body == b'The root: ROOT'

    assert captured.records == []
