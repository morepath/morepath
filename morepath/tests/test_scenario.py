from .fixtures import scenario
from .fixtures.scenario import app
from morepath import setup
import morepath

from webtest import TestApp as Client


def setup_module(module):
    morepath.disable_implicit()


def test_scenario():
    config = setup()
    config.scan(scenario)
    config.commit()

    c = Client(app.Root())

    response = c.get('/document')
    assert response.body == b'Document root'

    response = c.get('/foo')
    assert response.body == b'Generic root'

    response = c.get('/document/a')
    assert response.body == b'Document model a'

    response = c.get('/foo/a')
    assert response.body == b'Generic model a'

    response = c.get('/')
    assert response.json == ['/foo/a', '/document/b']

    response = c.get('/foo/a/link')
    assert response.body == '/document/c'

    response = c.get('/document/a/link')
    assert response.body == '/foo/d'
