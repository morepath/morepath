import logging
import morepath
import pytest

from .fixtures import basic


class Handler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super(Handler, self).__init__(level)
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture(scope='module')
def setup_amount():
    log = logging.getLogger('morepath.config')

    test_handler = Handler()

    log.addHandler(test_handler)
    log.setLevel(logging.DEBUG)

    config = morepath.setup()
    config.commit()

    # multiply this by 2, as the application subclass always
    # repeats all setup directives again.
    # XXX This will fail for deeper inheritance
    return len(test_handler.records) * 2


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

    config = morepath.setup()

    class App(morepath.App):
        testing_config = config

    App.registry.app = App

    @App.path(path='')
    class Model(object):
        pass

    config.commit()

    messages = [r.getMessage() for r in test_handler.records]
    assert len(messages) == 1
    assert messages[0] == (
        "@morepath.tests.test_config_logging.App.path(path='') on "
        "<class 'morepath.tests.test_config_logging.Model'>")


def test_config_logging_fixture():
    log = logging.getLogger('morepath.directive.path')

    test_handler = Handler()

    log.addHandler(test_handler)
    log.setLevel(logging.DEBUG)

    config = morepath.setup()
    config.scan(basic)
    config.commit()

    messages = [r.getMessage() for r in test_handler.records]
    messages.sort()

    assert messages == [
        "@morepath.tests.fixtures.basic.app.path("
        "model=<class 'morepath.tests.fixtures.basic.Model'>, "
        "path='{id}') on morepath.tests.fixtures.basic.get_model",
        "@morepath.tests.fixtures.basic.app.path(path='/') on "
        "<class 'morepath.tests.fixtures.basic.Root'>"
    ]
