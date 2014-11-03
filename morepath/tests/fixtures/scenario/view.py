from . import model
from . import app


@app.Root.json(model=model.RootRoot)
def root_root_default(self, request):
    return [request.link(model.GenericModel('a', 'foo')),
            request.link(model.DocumentModel('b'))]


@app.Generic.view(model=model.GenericRoot)
def generic_root_default(self, request):
    return "Generic root"


@app.Generic.view(model=model.GenericModel)
def generic_model_default(self, request):
    return "Generic model %s" % self.id


@app.Generic.view(model=model.GenericModel, name='link')
def generic_model_link(self, request):
    return request.link(model.DocumentModel('c'))


@app.Document.view(model=model.DocumentRoot)
def document_root_default(self, request):
    return "Document root"


@app.Document.view(model=model.DocumentModel)
def document_model_default(self, request):
    return "Document model %s" % self.id


@app.Document.view(model=model.DocumentModel, name='link')
def document_model_link(self, request):
    return request.link(model.GenericModel('d', 'foo'))
