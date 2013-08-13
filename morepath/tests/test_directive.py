from .fixtures import basic, nested
from morepath import setup
from morepath.config import Config
from morepath.request import Response
from werkzeug.test import Client

def test_basic():
    setup()
    basic.app.clear()
    
    config = Config()
    config.scan(basic)
    config.app(basic.app)
    config.commit()
    
    c = Client(basic.app, Response)
    
    response = c.get('/foo')

    assert response.data == 'The resource for model: foo'

    response = c.get('/foo/link')
    assert response.data == 'foo'

# def test_basic_root():
#     setup()
#     basic.app.clear()
    
#     config = Config()
#     config.scan(basic)
#     config.app(basic.app)
#     config.commit()
    
#     c = Client(basic.app, Response)
    
#     response = c.get('/')

#     assert response.data == 'The resource for model: foo'

#     response = c.get('/link')
#     assert response.data == 'foo'
    
def test_nested():
    setup()
    nested.outer_app.clear()
    nested.app.clear()

    config = Config()
    config.scan(nested)
    config.app(nested.outer_app)
    config.app(nested.app)
    config.commit()
    
    c = Client(nested.outer_app, Response)

    response = c.get('/inner/foo')

    assert response.data == 'The resource for model: foo'

    response = c.get('/inner/foo/link')
    assert response.data == 'inner/foo'
