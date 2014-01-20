import morepath
from morepath import setup
from morepath.request import Response
from morepath.converter import Converter
from morepath.error import DirectiveReportError

from werkzeug.test import Client
import pytest


def test_simple_path_one_step():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self):
            pass

    @app.model(model=Model, path='simple')
    def get_model():
        return Model()

    @app.view(model=Model)
    def default(request, model):
        return "View"

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/simple')
    assert response.data == 'View'

    response = c.get('/simple/link')
    assert response.data == '/simple'


def test_simple_path_two_steps():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self):
            pass

    @app.model(model=Model, path='one/two')
    def get_model():
        return Model()

    @app.view(model=Model)
    def default(request, model):
        return "View"

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/one/two')
    assert response.data == 'View'

    response = c.get('/one/two/link')
    assert response.data == '/one/two'


def test_variable_path_one_step():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, name):
            self.name = name

    @app.model(model=Model, path='{name}')
    def get_model(name):
        return Model(name)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.name

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/foo')
    assert response.data == 'View: foo'

    response = c.get('/foo/link')
    assert response.data == '/foo'


def test_variable_path_two_steps():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, name):
            self.name = name

    @app.model(model=Model, path='document/{name}')
    def get_model(name):
        return Model(name)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.name

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/document/foo')
    assert response.data == 'View: foo'

    response = c.get('/document/foo/link')
    assert response.data == '/document/foo'


def test_variable_path_two_variables():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, name, version):
            self.name = name
            self.version = version

    @app.model(model=Model, path='{name}-{version}')
    def get_model(name, version):
        return Model(name, version)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s %s" % (model.name, model.version)

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('foo-one')
    assert response.data == 'View: foo one'

    response = c.get('/foo-one/link')
    assert response.data == '/foo-one'


def test_variable_path_explicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='{id}',
               converters=dict(id=Converter(int)))
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s (%s)" % (model.id, type(model.id))

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('1')
    assert response.data == "View: 1 (<type 'int'>)"

    response = c.get('/1/link')
    assert response.data == '/1'

    response = c.get('broken')
    assert response.status == '404 NOT FOUND'


def test_variable_path_implicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='{id}')
    def get_model(id=0):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s (%s)" % (model.id, type(model.id))

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('1')
    assert response.data == "View: 1 (<type 'int'>)"

    response = c.get('/1/link')
    assert response.data == '/1'

    response = c.get('broken')
    assert response.status == '404 NOT FOUND'


def test_variable_path_explicit_trumps_implicit():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='{id}',
               converters=dict(id=Converter(int)))
    def get_model(id='foo'):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s (%s)" % (model.id, type(model.id))

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('1')
    assert response.data == "View: 1 (<type 'int'>)"

    response = c.get('/1/link')
    assert response.data == '/1'

    response = c.get('broken')
    assert response.status == '404 NOT FOUND'


def test_url_parameter_explicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='/',
               converters=dict(id=Converter(int)))
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s (%s)" % (model.id, type(model.id))

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/?id=1')
    assert response.data == "View: 1 (<type 'int'>)"

    response = c.get('/link?id=1')
    assert response.data == '/?id=1'

    response = c.get('/?id=broken')
    assert response.status == '400 BAD REQUEST'

    response = c.get('/')
    assert response.data == "View: None (<type 'NoneType'>)"


def test_url_parameter_implicit_converter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='/')
    def get_model(id=0):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s (%s)" % (model.id, type(model.id))

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/?id=1')
    assert response.data == "View: 1 (<type 'int'>)"

    response = c.get('/link?id=1')
    assert response.data == '/?id=1'

    response = c.get('/?id=broken')
    assert response.status == '400 BAD REQUEST'

    response = c.get('/')
    assert response.data == "View: 0 (<type 'int'>)"


def test_url_parameter_explicit_trumps_implicit():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='/',
               converters=dict(id=Converter(int)))
    def get_model(id='foo'):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s (%s)" % (model.id, type(model.id))

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/?id=1')
    assert response.data == "View: 1 (<type 'int'>)"

    response = c.get('/link?id=1')
    assert response.data == '/?id=1'

    response = c.get('/?id=broken')
    assert response.status == '400 BAD REQUEST'

    response = c.get('/')
    assert response.data == "View: foo (<type 'str'>)"


def test_decode_encode():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    def my_decode(s):
        return s + 'ADD'

    def my_encode(s):
        return s[:-len('ADD')]

    @app.model(model=Model, path='/',
               converters=dict(id=Converter(my_decode, my_encode)))
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.id

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/?id=foo')
    assert response.data == "View: fooADD"

    response = c.get('/link?id=foo')
    assert response.data == '/?id=foo'


def test_unknown_converter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, d):
            self.d = d

    class Unknown(object):
        pass

    @app.model(model=Model, path='/')
    def get_model(d=Unknown()):
        return Model(d)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.d

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    with pytest.raises(DirectiveReportError):
        config.commit()


def test_default_date_converter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, d):
            self.d = d

    from datetime import date

    @app.model(model=Model, path='/')
    def get_model(d=date(2011, 1, 1)):
        return Model(d)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.d

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/?d=20121110')
    assert response.data == "View: 2012-11-10"

    response = c.get('/')
    assert response.data == "View: 2011-01-01"

    response = c.get('/link?d=20121110')
    assert response.data == '/?d=20121110'

    response = c.get('/link')
    assert response.data == '/?d=20110101'

    response = c.get('/?d=broken')
    assert response.status == '400 BAD REQUEST'


def test_default_datetime_converter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, d):
            self.d = d

    from datetime import datetime

    @app.model(model=Model, path='/')
    def get_model(d=datetime(2011, 1, 1, 10, 30)):
        return Model(d)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.d

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/?d=20121110T144530')
    assert response.data == "View: 2012-11-10 14:45:30"

    response = c.get('/')
    assert response.data == "View: 2011-01-01 10:30:00"

    response = c.get('/link?d=20121110T144500')
    assert response.data == '/?d=20121110T144500'

    response = c.get('/link')
    assert response.data == '/?d=20110101T103000'

    response = c.get('/?d=broken')
    assert response.status == '400 BAD REQUEST'


def test_custom_date_converter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, d):
            self.d = d

    from datetime import date
    from time import strptime, mktime

    def date_decode(s):
        return date.fromtimestamp(mktime(strptime(s, '%d-%m-%Y')))

    def date_encode(d):
        return d.strftime('%d-%m-%Y')

    @app.converter(type=date)
    def date_converter():
        return Converter(date_decode, date_encode)

    @app.model(model=Model, path='/')
    def get_model(d=date(2011, 1, 1)):
        return Model(d)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.d

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/?d=10-11-2012')
    assert response.data == "View: 2012-11-10"

    response = c.get('/')
    assert response.data == "View: 2011-01-01"

    response = c.get('/link?d=10-11-2012')
    assert response.data == '/?d=10-11-2012'

    response = c.get('/link')
    assert response.data == '/?d=01-01-2011'

    response = c.get('/?d=broken')
    assert response.status == '400 BAD REQUEST'


def test_variable_path_parameter_required_no_default():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='', required=['id'])
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.id

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/?id=a')
    assert response.data == "View: a"

    response = c.get('/')
    assert response.status == '400 BAD REQUEST'


def test_variable_path_parameter_required_with_default():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='', required=['id'])
    def get_model(id='b'):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.id

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/?id=a')
    assert response.data == "View: a"

    response = c.get('/')
    assert response.status == '400 BAD REQUEST'

def test_type_hints_and_converters():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, d):
            self.d = d

    from datetime import date

    @app.model(model=Model, path='', converters=dict(d=date))
    def get_model(d):
        return Model(d)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.d

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/?d=20140120')
    assert response.data == "View: 2014-01-20"

    response = c.get('/link?d=20140120')
    assert response.data == '/?d=20140120'

def test_link_for_none_means_no_parameter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id):
            self.id = id

    @app.model(model=Model, path='')
    def get_model(id):
        return Model(id)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s" % model.id

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/')
    assert response.data == "View: None"

    response = c.get('/link')
    assert response.data == '/'



def test_path_and_url_parameter_converter():
    config = setup()
    app = morepath.App(testing_config=config)

    class Model(object):
        def __init__(self, id, param):
            self.id = id
            self.param = param

    from datetime import date
    @app.model(model=Model, path='/{id}', converters=dict(param=date))
    def get_model(id=0, param=None):
        return Model(id, param)

    @app.view(model=Model)
    def default(request, model):
        return "View: %s %s" % (model.id, model.param)

    @app.view(model=Model, name='link')
    def link(request, model):
        return request.link(model)

    config.commit()

    c = Client(app, Response)

    response = c.get('/1/link')
    assert response.data == '/1'
