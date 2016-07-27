import morepath
from webtest import TestApp as Client
from morepath.error import LinkError, ConflictError
import pytest


def test_defer_links():

    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path='')
    class RootModel(object):
        pass

    @Root.view(model=RootModel)
    def root_model_default(self, request):
        return request.link(SubModel())

    @Root.view(model=RootModel, name='class_link')
    def root_model_class_link(self, request):
        return request.class_link(SubModel)

    @Sub.path(path='')
    class SubModel(object):
        pass

    @Root.mount(app=Sub, path='sub')
    def mount_sub():
        return Sub()

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app, obj):
        return app.child(Sub())

    c = Client(Root())

    response = c.get('/')
    assert response.body == b'http://localhost/sub'

    with pytest.raises(LinkError):
        c.get('/class_link')


def test_defer_view():
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path='')
    class RootModel(object):
        pass

    @Root.json(model=RootModel)
    def root_model_default(self, request):
        return request.view(SubModel())

    @Sub.path(path='')
    class SubModel(object):
        pass

    @Sub.json(model=SubModel)
    def submodel_default(self, request):
        return {'hello': 'world'}

    @Root.mount(app=Sub, path='sub')
    def mount_sub():
        return Sub()

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app, obj):
        return app.child(Sub())

    c = Client(Root())

    response = c.get('/')
    assert response.json == {'hello': 'world'}


def test_defer_view_predicates():
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path='')
    class RootModel(object):
        pass

    @Root.json(model=RootModel)
    def root_model_default(self, request):
        return request.view(SubModel(), name='edit')

    @Sub.path(path='')
    class SubModel(object):
        pass

    @Sub.json(model=SubModel, name='edit')
    def submodel_edit(self, request):
        return {'hello': 'world'}

    @Root.mount(app=Sub, path='sub')
    def mount_sub():
        return Sub()

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app, obj):
        return app.child(Sub())

    c = Client(Root())

    response = c.get('/')
    assert response.json == {'hello': 'world'}


def test_defer_view_missing_view():
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path='')
    class RootModel(object):
        pass

    @Root.json(model=RootModel)
    def root_model_default(self, request):
        return {'not_found': request.view(SubModel(), name='unknown')}

    @Sub.path(path='')
    class SubModel(object):
        pass

    @Sub.json(model=SubModel, name='edit')
    def submodel_edit(self, request):
        return {'hello': 'world'}

    @Root.mount(app=Sub, path='sub')
    def mount_sub():
        return Sub()

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app, obj):
        return app.child(Sub())

    c = Client(Root())

    response = c.get('/')
    assert response.json == {'not_found': None}


def test_defer_links_mount_parameters():
    class root(morepath.App):
        pass

    class sub(morepath.App):
        pass

        def __init__(self, name):
            self.name = name

    @root.path(path='')
    class RootModel(object):
        pass

    @root.view(model=RootModel)
    def root_model_default(self, request):
        return request.link(SubModel('foo'))

    class SubModel(object):
        def __init__(self, name):
            self.name = name

    @sub.path(path='', model=SubModel)
    def get_sub_model(request):
        return SubModel(request.app.name)

    @root.mount(app=sub, path='{mount_name}',
                variables=lambda a: {'mount_name': a.name})
    def mount_sub(mount_name):
        return sub(name=mount_name)

    @root.defer_links(model=SubModel)
    def defer_links_sub_model(app, obj):
        return app.child(sub(name=obj.name))

    c = Client(root())

    response = c.get('/')
    assert response.body == b'http://localhost/foo'


def test_defer_link_acquisition():
    class root(morepath.App):
        pass

    class sub(morepath.App):
        pass

    @root.path(path='model/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @root.view(model=Model)
    def model_default(self, request):
        return "Hello"

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.view(model=SubModel)
    def sub_model_default(self, request):
        return request.link(Model('foo'))

    @root.mount(app=sub, path='sub')
    def mount_sub(obj, app):
        return app.child(sub())

    @sub.defer_links(model=Model)
    def get_parent(app, obj):
        return app.parent

    c = Client(root())

    response = c.get('/sub')
    assert response.body == b'http://localhost/model/foo'


def test_defer_view_acquisition():
    class root(morepath.App):
        pass

    class sub(morepath.App):
        pass

    @root.path(path='model/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @root.json(model=Model)
    def model_default(self, request):
        return {"Hello": "World"}

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.json(model=SubModel)
    def sub_model_default(self, request):
        return request.view(Model('foo'))

    @root.mount(app=sub, path='sub')
    def mount_sub(obj, app):
        return app.child(sub())

    @sub.defer_links(model=Model)
    def get_parent(app, obj):
        return app.parent

    c = Client(root())

    response = c.get('/sub')
    assert response.json == {"Hello": "World"}


def test_defer_link_acquisition_blocking():
    class root(morepath.App):
        pass

    class sub(morepath.App):
        pass

    @root.path(path='model/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @root.view(model=Model)
    def model_default(self, request):
        return "Hello"

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.view(model=SubModel)
    def sub_model_default(self, request):
        try:
            return request.link(Model('foo'))
        except LinkError:
            return "link error"

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    # no defer_links_to_parent

    c = Client(root())

    response = c.get('/sub')
    assert response.body == b'link error'


def test_defer_view_acquisition_blocking():
    class root(morepath.App):
        pass

    class sub(morepath.App):
        pass

    @root.path(path='model/{id}')
    class Model(object):
        def __init__(self, id):
            self.id = id

    @root.json(model=Model)
    def model_default(self, request):
        return {"Hello": "World"}

    @sub.path(path='')
    class SubModel(object):
        pass

    @sub.json(model=SubModel)
    def sub_model_default(self, request):
        return request.view(Model('foo')) is None

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    # no defer_links_to_parent

    c = Client(root())

    response = c.get('/sub')
    assert response.json is True


def test_defer_link_should_not_cause_web_views_to_exist():
    class root(morepath.App):
        pass

    class sub(morepath.App):
        pass

    @root.path(path='')
    class Model(object):
        pass

    @root.view(model=Model)
    def model_default(self, request):
        return "Hello"

    @root.view(model=Model, name='extra')
    def model_extra(self, request):
        return "Extra"

    # note inheritance from model. we still don't
    # want the extra view to show up on the web
    @sub.path(path='')
    class SubModel(Model):
        pass

    @sub.view(model=SubModel)
    def sub_model_default(self, request):
        return request.link(Model())

    @root.mount(app=sub, path='sub')
    def mount_sub():
        return sub()

    @sub.defer_links(model=Model)
    def get_parent(app, obj):
        return app.parent

    c = Client(root())

    response = c.get('/sub')
    assert response.body == b'http://localhost/'

    c.get('/sub/+extra', status=404)


def test_defer_link_to_parent_from_root():
    class root(morepath.App):
        pass

    class sub(morepath.App):
        pass

    @root.path(path='')
    class Model(object):
        pass

    class OtherModel(object):
        pass

    @root.view(model=Model)
    def model_default(self, request):
        return request.link(OtherModel())

    @root.defer_links(model=OtherModel)
    def get_parent(app, obj):
        return app.parent

    c = Client(root())

    with pytest.raises(LinkError):
        c.get('/')


def test_special_link_overrides_deferred_link():
    class root(morepath.App):
        pass

    class alpha(morepath.App):
        pass

    class AlphaModel(object):
        pass

    class SpecialAlphaModel(AlphaModel):
        pass

    @root.mount(app=alpha, path='alpha')
    def mount_alpha():
        return alpha()

    @root.path(path='')
    class RootModel(object):
        pass

    @root.path(model=SpecialAlphaModel, path='roots_alpha')
    def get_root_alpha():
        return SpecialAlphaModel()

    @root.view(model=RootModel)
    def root_model_default(self, request):
        return request.link(AlphaModel())

    @root.view(model=RootModel, name='special')
    def root_model_special(self, request):
        return request.link(SpecialAlphaModel())

    @alpha.path(path='', model=AlphaModel)
    def get_alpha():
        return AlphaModel()

    @root.defer_links(model=AlphaModel)
    def defer_links_alpha(app, obj):
        return app.child(alpha())

    c = Client(root())

    response = c.get('/')
    assert response.body == b'http://localhost/alpha'

    response = c.get('/special')
    assert response.body == b'http://localhost/roots_alpha'


def test_deferred_deferred_link():
    class root(morepath.App):
        pass

    class alpha(morepath.App):
        pass

    class beta(morepath.App):
        pass

    @root.path(path='')
    class RootModel(object):
        pass

    @root.view(model=RootModel)
    def root_model_default(self, request):
        return request.link(AlphaModel())

    @alpha.path(path='')
    class AlphaModel(object):
        pass

    @beta.path(path='')
    class BetaModel(object):
        pass

    @beta.view(model=BetaModel)
    def beta_model_default(self, request):
        return request.link(AlphaModel())

    @root.mount(app=alpha, path='alpha')
    def mount_alpha():
        return alpha()

    @root.mount(app=beta, path='beta')
    def mount_beta():
        return beta()

    @beta.defer_links(model=AlphaModel)
    def defer_links_parent(app, obj):
        return app.parent

    @root.defer_links(model=AlphaModel)
    def defer_links_alpha(app, obj):
        return app.child(alpha())

    c = Client(root())

    response = c.get('/')
    assert response.body == b'http://localhost/alpha'

    response = c.get('/beta')
    assert response.body == b'http://localhost/alpha'


def test_deferred_deferred_view():
    class root(morepath.App):
        pass

    class alpha(morepath.App):
        pass

    class beta(morepath.App):
        pass

    @root.path(path='')
    class RootModel(object):
        pass

    @root.json(model=RootModel)
    def root_model_default(self, request):
        return request.view(AlphaModel())

    @alpha.path(path='')
    class AlphaModel(object):
        pass

    @alpha.json(model=AlphaModel)
    def alpha_model_default(self, request):
        return {"model": "alpha"}

    @beta.path(path='')
    class BetaModel(object):
        pass

    @beta.json(model=BetaModel)
    def beta_model_default(self, request):
        return request.view(AlphaModel())

    @root.mount(app=alpha, path='alpha')
    def mount_alpha():
        return alpha()

    @root.mount(app=beta, path='beta')
    def mount_beta():
        return beta()

    @beta.defer_links(model=AlphaModel)
    def defer_links_parent(app, obj):
        return app.parent

    @root.defer_links(model=AlphaModel)
    def defer_links_alpha(app, obj):
        return app.child(alpha())

    c = Client(root())

    response = c.get('/')
    assert response.json == {'model': 'alpha'}

    response = c.get('/beta')
    assert response.json == {'model': 'alpha'}


def test_deferred_view_has_app_of_defer():
    class root(morepath.App):
        pass

    class alpha(morepath.App):
        pass

    class beta(morepath.App):
        pass

    @root.mount(app=alpha, path='alpha')
    def mount_alpha():
        return alpha()

    @root.mount(app=beta, path='beta')
    def mount_beta():
        return beta()

    @root.path(path='')
    class RootModel(object):
        pass

    @alpha.path(path='')
    class AlphaModel(object):
        pass

    @alpha.json(model=AlphaModel)
    def alpha_model_default(self, request):
        if request.app.__class__ == alpha:
            return 'correct'
        else:
            return 'wrong'

    @beta.path(path='')
    class BetaModel(object):
        pass

    @beta.json(model=BetaModel)
    def beta_model_default(self, request):
        return request.view(AlphaModel())

    @beta.defer_links(model=AlphaModel)
    def defer_links_parent(app, obj):
        return app.parent.child('alpha')

    c = Client(root())

    response = c.get('/beta')
    assert response.json == 'correct'


def test_deferred_loop():
    class root(morepath.App):
        pass

    class alpha(morepath.App):
        pass

    @root.path(path='')
    class RootModel(object):
        pass

    # not actually exposed with path anywhere!
    class Model(object):
        pass

    @root.json(model=RootModel)
    def root_model_default(self, request):
        return request.link(Model())

    @root.mount(app=alpha, path='alpha')
    def mount_alpha():
        return alpha()

    # setup a loop: defer to parent and back to child!
    @alpha.defer_links(model=Model)
    def defer_links_parent(app, obj):
        return app.parent

    @root.defer_links(model=Model)
    def defer_links_alpha(app, obj):
        return app.child(alpha())

    c = Client(root())

    with pytest.raises(LinkError) as ex:
        c.get('/')

    assert 'Circular' in str(ex.value)


@pytest.mark.skip(reason='Infinite loop (#479)', run=False)
def test_deferred_loop_siblings():
    # https://github.com/morepath/morepath/issues/479
    class Root(morepath.App):
        pass

    class Alpha(morepath.App):
        pass

    class Beta(morepath.App):
        pass

    @Root.path(path='')
    class RootModel(object):
        pass

    # not actually exposed with path anywhere!
    class Model(object):
        pass

    @Root.json(model=RootModel)
    def root_model_default(self, request):
        return request.link(Model())

    @Root.defer_links(model=Model)
    def defer_links_alpha(app, obj):
        return app.child(Alpha())

    @Root.mount(app=Alpha, path='alpha')
    def mount_alpha():
        return Alpha()

    @Root.mount(app=Beta, path='beta')
    def mount_beta():
        return Beta()

    # setup a loop: defer to sibling and back
    @Alpha.defer_links(model=Model)
    def defer_links_to_beta(app, obj):
        return app.sibling(Beta())

    @Beta.defer_links(model=Model)
    def defer_links_to_alpha(app, obj):
        return app.sibling(Alpha())

    c = Client(Root())

    with pytest.raises(LinkError) as ex:
        c.get('/')

    assert 'Circular' in str(ex.value)


# see issue #342
def test_defer_link_scenario():
    class App(morepath.App):
        pass

    class Child(morepath.App):
        pass

    class Document(object):
        pass

    @App.mount(app=Child, path='child')
    def mount_child():
        return Child()

    @App.defer_links(model=Document)
    def defer_document(app, doc):
        return app.child(Child())

    @App.path(path='')
    class Root(object):
        pass

    @App.json(model=Root)
    def root_view(self, request):
        return {
            'link': request.link(Document()),
            'view': request.view(Document())
        }

    # if this is commented out, the Child app's view for Document
    # will be used by root_view, which is surprising.
    @App.json(model=Document)
    def app_document_default(self, request):
        return {
            'app': 'App'
        }

    @Child.path('', model=Document)
    def get_document():
        return Document()

    @Child.json(model=Document)
    def document_default(self, request):
        return {
            'app': 'Child',
        }

    c = Client(App())

    response = c.get('/child')

    assert response.json == {'app': 'Child'}

    response = c.get('/')

    # it is rather surprising that the view is not deferred to Child if there
    # is a view defined for App. It is according to spec: the app uses
    # its own behavior if it's there, and only defers afterwards. Is this
    # really what we want, though?
    assert response.json == {
        'link': 'http://localhost/child',
        'view': {'app': 'App'}
    }


def test_defer_class_links_without_variables():
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path='')
    class RootModel(object):
        pass

    @Root.view(model=RootModel)
    def root_model_default(self, request):
        return request.class_link(SubModel)

    @Sub.path(path='')
    class SubModel(object):
        pass

    @Root.mount(app=Sub, path='sub')
    def mount_sub():
        return Sub()

    @Root.defer_class_links(model=SubModel, variables=lambda obj: {})
    def defer_class_links_sub_model(app, model, variables):
        return app.child(Sub())

    c = Client(Root())

    response = c.get('/')
    assert response.body == b'http://localhost/sub'


def test_defer_class_links_with_variables():
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path='')
    class RootModel(object):
        pass

    @Root.view(model=RootModel)
    def root_model_default(self, request):
        return request.class_link(SubModel, variables=dict(name='foo'))

    @Sub.path(path='{name}')
    class SubModel(object):
        def __init__(self, name):
            self.name = name

    @Root.mount(app=Sub, path='sub')
    def mount_sub():
        return Sub()

    @Root.defer_class_links(model=SubModel,
                            variables=lambda obj: {'name': obj.name})
    def defer_class_links_sub_model(app, model, variables):
        return app.child(Sub())

    c = Client(Root())

    response = c.get('/')
    assert response.body == b'http://localhost/sub/foo'


def test_deferred_class_link_loop():
    class Root(morepath.App):
        pass

    class Alpha(morepath.App):
        pass

    @Root.path(path='')
    class RootModel(object):
        pass

    # not actually exposed with path anywhere!
    class SubModel(object):
        pass

    @Root.view(model=RootModel)
    def root_model_default(self, request):
        return request.class_link(SubModel)

    @Root.mount(app=Alpha, path='alpha')
    def mount_alpha():
        return Alpha()

    # setup a loop: defer to parent and back to child!
    @Alpha.defer_class_links(model=SubModel, variables=lambda obj: {})
    def defer_class_links_parent(app, obj, variables):
        return app.parent

    @Root.defer_class_links(model=SubModel, variables=lambda obj: {})
    def defer_class_links_alpha(app, obj, variables):
        return app.child(Alpha())

    c = Client(Root())

    with pytest.raises(LinkError) as ex:
        c.get('/')

    assert 'Circular' in str(ex.value)


def test_link_uses_defer_class_links():
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path='')
    class RootModel(object):
        pass

    @Root.view(model=RootModel)
    def root_model_default(self, request):
        return request.link(SubModel('foo'))

    @Sub.path(path='{name}')
    class SubModel(object):
        def __init__(self, name):
            self.name = name

    @Root.mount(app=Sub, path='sub')
    def mount_sub():
        return Sub()

    @Root.defer_class_links(model=SubModel,
                            variables=lambda obj: {'name': obj.name})
    def defer_class_links_sub_model(app, model, variables):
        return app.child(Sub())

    c = Client(Root())

    response = c.get('/')
    assert response.body == b'http://localhost/sub/foo'


def test_defer_links_and_defer_links_conflict():
    class Root(morepath.App):
        pass

    class Sub(morepath.App):
        pass

    @Root.path(path='')
    class RootModel(object):
        pass

    @Root.view(model=RootModel)
    def root_model_default(self, request):
        return request.link(SubModel('foo'))

    @Sub.path(path='{name}')
    class SubModel(object):
        def __init__(self, name):
            self.name = name

    @Root.mount(app=Sub, path='sub')
    def mount_sub():
        return Sub()

    @Root.defer_links(model=SubModel)
    def defer_links_sub_model(app, obj):
        return app.chidl(Sub())

    @Root.defer_class_links(model=SubModel,
                            variables=lambda obj: {'name': obj.name})
    def defer_class_links_sub_model(app, model, variables):
        return app.child(Sub())

    with pytest.raises(ConflictError):
        Root.commit()
