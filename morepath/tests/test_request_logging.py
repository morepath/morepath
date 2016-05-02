import morepath
from webtest import TestApp as Client
import logging

from .capturelog import CaptureLog


def test_logging():
    class App(morepath.App):
        pass

    class Model(object):
        def __init__(self, id):
            self.id = id

    @App.path(model=Model, path='{id}')
    def get_model(id):
        return Model(id)

    @App.view(model=Model)
    def default(self, request):
        return "The view for model: %s" % self.id

    App.commit()

    c = Client(App())

    with CaptureLog('morepath', logging.DEBUG) as captured:
        response = c.get('/foo')
        assert response.body == b'The view for model: foo'

    r = captured.records
    assert len(r) == 4
    assert r[0].getMessage() == 'Find model obj for path: /foo'
    assert r[1].getMessage().startswith('Found model obj: ')
    assert r[2].getMessage().startswith("Calling view function ")
    assert r[3].getMessage().startswith("Rendering view for content")
