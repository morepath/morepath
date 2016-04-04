import importscan
import dectate
import logging
import morepath

from .fixtures import basic
from morepath.compat import PY3


class Handler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super(Handler, self).__init__(level)
        self.records = []

    def emit(self, record):
        self.records.append(record)


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


def test_simple_config_logging():
    log = logging.getLogger('morepath.directive.path')

    test_handler = Handler()

    log.addHandler(test_handler)
    log.setLevel(logging.DEBUG)

    class App(morepath.App):
        pass

    @App.path(path='')
    class Model(object):
        pass

    dectate.commit(App)

    messages = [r.getMessage() for r in test_handler.records]
    assert len(messages) == 1
    if PY3:
        expected = (
            "@morepath.tests.test_config_logging.App.path(path='') on "
            "<class 'morepath.tests.test_config_logging."
            "test_simple_config_logging.<locals>.Model'>")
    else:
        expected = (
            "@morepath.tests.test_config_logging.App.path(path='') on "
            "<class 'morepath.tests.test_config_logging.Model'>")
    assert messages[0] == expected


def test_config_logging_fixture():
    log = logging.getLogger('morepath.directive.path')

    test_handler = Handler()

    log.addHandler(test_handler)
    log.setLevel(logging.DEBUG)

    importscan.scan(basic)
    dectate.commit(basic.app)

    messages = [r.getMessage() for r in test_handler.records]
    messages.sort()

    assert messages == [
        "@morepath.tests.fixtures.basic.app.path("
        "model=<class 'morepath.tests.fixtures.basic.Model'>, "
        "path='{id}') on morepath.tests.fixtures.basic.get_model",
        "@morepath.tests.fixtures.basic.app.path(path='/') on "
        "<class 'morepath.tests.fixtures.basic.Root'>"
    ]
