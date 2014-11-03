from . import model
from . import app


@app.Root.path(path='', model=model.RootRoot)
def get_root_root():
    return model.RootRoot()


@app.Generic.path(path='', model=model.GenericRoot)
def get_generic_root():
    return model.GenericRoot()


@app.Generic.path(path='{id}', model=model.GenericModel)
def get_generic_model(id, app):
    return model.GenericModel(id=id, name=app.name)


@app.Document.path(path='', model=model.DocumentRoot)
def get_document_root():
    return model.DocumentRoot()


@app.Document.path(path='{id}', model=model.DocumentModel)
def get_document_model(id):
    return model.DocumentModel(id)
