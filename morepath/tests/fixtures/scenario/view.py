from __future__ import annotations

from typing import TYPE_CHECKING

from . import app, model

if TYPE_CHECKING:
    from morepath.request import Request


@app.Root.json(model=model.RootRoot)
def root_root_default(self: app.Root, request: Request) -> list[str]:
    return [
        request.link(model.GenericModel("a", "foo")),
        request.link(model.DocumentModel("b")),
    ]


@app.Generic.view(model=model.GenericRoot)
def generic_root_default(self: model.GenericRoot, request: Request) -> str:
    return "Generic root"


@app.Generic.view(model=model.GenericModel)
def generic_model_default(self: model.GenericModel, request: Request) -> str:
    return f"Generic model {self.id}"


@app.Generic.view(model=model.GenericModel, name="link")
def generic_model_link(self: model.GenericModel, request: Request) -> str:
    return request.link(model.DocumentModel("c"))


@app.Document.view(model=model.DocumentRoot)
def document_root_default(self: model.DocumentRoot, request: Request) -> str:
    return "Document root"


@app.Document.view(model=model.DocumentModel)
def document_model_default(self: model.DocumentModel, request: Request) -> str:
    return f"Document model {self.id}"


@app.Document.view(model=model.DocumentModel, name="link")
def document_model_link(self: model.DocumentModel, request: Request) -> str:
    return request.link(model.GenericModel("d", "foo"))
