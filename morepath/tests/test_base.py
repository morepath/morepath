from morepath.app import App
from morepath.config import Config
from morepath import setup
from morepath.request import Response
from werkzeug.test import Client


def test_base():
    setup()

    class Root(object):
        pass

    class Container(object):
        def __init__(self, id):
            self.id = id
            self.items = {}

        def add_item(self, item_id):
            result = Item(item_id, self)
            self.items[item_id] = result
            return result

    class Item(object):
        def __init__(self, id, parent):
            self.id = id
            self.parent = parent

    alpha = Container('alpha')
    beta = Container('beta')
    alpha.add_item('a')
    alpha.add_item('b')
    c = alpha.add_item('c')
    beta.add_item('d')
    e = beta.add_item('e')

    app = App()

    c = Config()
    c.action(app, app)
    c.action(app.root(), Root)

    def get_container(container_id):
        if container_id == 'alpha':
            return alpha
        elif container_id == 'beta':
            return beta
        return None

    c.action(
        app.model(
            model=Container,
            path="{container_id}",
            variables=lambda container: {'container_id': container.id}),
        get_container)

    def get_item(base, item_id):
        return base.items.get(item_id)

    c.action(
        app.model(model=Item,
                  path="{item_id}",
                  variables=lambda item: {'item_id': item.id},
                  base=Container,
                  get_base=lambda item: item.parent),
        get_item)

    c.action(
        app.view(model=Container),
        lambda request, model: 'container: %s' % model.id)
    c.action(
        app.view(model=Container, name='link'),
        lambda request, model: request.link(model))
    c.action(
        app.view(model=Item),
        lambda request, model: 'item: %s' % model.id)
    c.action(
        app.view(model=Item, name='link'),
        lambda request, model: request.link(model))
    c.action(
        app.view(model=Item, name='otherlink'),
        lambda request, model: request.link(e))
    c.commit()

    c = Client(app, Response)

    response = c.get('/alpha')
    assert response.data == 'container: alpha'
    response = c.get('/beta')
    assert response.data == 'container: beta'
    response = c.get('/alpha/a')
    assert response.data == 'item: a'
    response = c.get('/beta/e')
    assert response.data == 'item: e'
    response = c.get('/alpha/e')
    assert response.status == '404 NOT FOUND'

    response = c.get('/alpha/@@link')
    assert response.data == 'alpha'
    response = c.get('/alpha/a/link')
    assert response.data == 'alpha/a'
    response = c.get('/alpha/a/otherlink')
    assert response.data == 'beta/e'
