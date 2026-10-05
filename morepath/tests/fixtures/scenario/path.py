from . import app, model


@app.Root.path(path="", model=model.RootRoot)
def get_root_root() -> model.RootRoot:
    return model.RootRoot()


@app.Generic.path(path="", model=model.GenericRoot)
def get_generic_root() -> model.GenericRoot:
    return model.GenericRoot()


@app.Generic.path(path="{id}", model=model.GenericModel)
def get_generic_model(id: str, app: app.Generic) -> model.GenericModel:
    return model.GenericModel(id=id, name=app.name)


@app.Document.path(path="", model=model.DocumentRoot)
def get_document_root() -> model.DocumentRoot:
    return model.DocumentRoot()


@app.Document.path(path="{id}", model=model.DocumentModel)
def get_document_model(id: str) -> model.DocumentModel:
    return model.DocumentModel(id)
