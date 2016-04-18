import logging
import morepath

from .fixtures import basic
from webtest import TestApp as Client


class Handler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super(Handler, self).__init__(level)
        self.records = []

    def emit(self, record):
        self.records.append(record)

    def clear(self):
        self.records[:] = []


def test_intercept_logging():
    log = logging.getLogger('my_logger')

    test_handler = Handler()

    log.addHandler(test_handler)
    # default is NOTSET which would propagate log to parent
    # logger instead of handling it directly.
    log.setLevel(logging.DEBUG)
    log.debug("This is a log message")

    assert len(test_handler.records) == 1
    assert test_handler.records[0].getMessage() == 'This is a log message'


def test_config_logging_implicit_commit():
    log = logging.getLogger('morepath.directive.path')

    test_handler = Handler()

    log.addHandler(test_handler)
    log.setLevel(logging.DEBUG)

    class App(morepath.App):
        pass

    @App.path(path='')
    class Model(object):
        pass

    @App.view(model=Model)
    def default(self, request):
        return "View"

    c = Client(App())
    response = c.get('/')
    assert response.body == b'View'

    messages = [r.getMessage() for r in test_handler.records]
    assert messages == [
        "@morepath.tests.test_config_logging.App.path(path='') on {!r}"
        .format(Model)]

    # Instantiating and serving a second app does not trigger a new
    # commit:
    test_handler.clear()
    c = Client(App())
    response = c.get('/')
    assert response.body == b'View'
    messages = [r.getMessage() for r in test_handler.records]
    assert messages == []


def test_config_logging_explicit_commit():
    log = logging.getLogger('morepath.directive.path')

    test_handler = Handler()

    log.addHandler(test_handler)
    log.setLevel(logging.DEBUG)

    # Manually commit the app:
    assert basic.app.commit() == {basic.app}

    messages = [r.getMessage() for r in test_handler.records]
    messages.sort()

    assert messages == [
        "@morepath.tests.fixtures.basic.app.path("
        "model=<class 'morepath.tests.fixtures.basic.Model'>, "
        "path='{id}') on morepath.tests.fixtures.basic.get_model",
        "@morepath.tests.fixtures.basic.app.path(path='/') on "
        "<class 'morepath.tests.fixtures.basic.Root'>"
    ]

    # Instantiating and serving the app does not trigger a new commit:
    test_handler.clear()
    c = Client(basic.app())
    response = c.get('/')
    assert response.body == b'The root: ROOT'
    messages = [r.getMessage() for r in test_handler.records]
    assert messages == []
