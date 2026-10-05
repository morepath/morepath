import morepath

from . import model


class Root(morepath.App):
    pass


class Generic(morepath.App):
    def __init__(self, name: str):
        self.name = name


class Document(morepath.App):
    pass


@Root.mount(app=Generic, path="{name}")
def get_generic_app(name: str) -> Generic:
    return Generic(name)


@Root.mount(app=Document, path="document")
def get_document_app() -> Document:
    return Document()


@Root.defer_links(model.GenericModel)
def defer_generic_app(app: Root, obj: model.GenericModel) -> Generic | None:
    return app.child(Generic(obj.name))


@Root.defer_links(model.DocumentModel)
def defer_document_app(app: Root, obj: model.DocumentModel) -> Document | None:
    return app.child(Document())


@Generic.defer_links(object)
def defer_generic_to_root(app: Generic, obj: object) -> morepath.App | None:
    return app.parent


@Document.defer_links(object)
def defer_document_to_root(app: Document, obj: object) -> morepath.App | None:
    return app.parent
