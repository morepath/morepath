from .fixtures import basic
from comparch import Registry, Lookup
from comparch import ChainClassLookup
from morepath.config import Config
from morepath.publish import publish
from morepath.interfaces import IRoot, IConsumer
from morepath.request import Request, Response
from morepath.app import global_app
from werkzeug.test import Client

def test_basic():
    config = Config()
    config.scan(basic)
    config.commit()
    
    c = Client(basic.app, Response)
    
    response = c.get('foo')

    assert response.data == 'The resource for model: foo'

    response = c.get('foo/link')
    assert response.data == 'myapp/foo'
   
