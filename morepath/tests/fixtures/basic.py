import morepath


class App(morepath.App):
    pass


@App.path(path="/")
class Root:
    def __init__(self) -> None:
        self.value = "ROOT"


class Model:
    def __init__(self, id: str) -> None:
        self.id = id


@App.path(model=Model, path="{id}")
def get_model(id: str) -> Model:
    return Model(id)


@App.view(model=Model)
def default(self: Model, request: morepath.Request) -> str:
    return f"The view for model: {self.id}"


@App.view(model=Model, name="link")
def link(self: Model, request: morepath.Request) -> str:
    return request.link(self)


@App.view(model=Model, name="json", render=morepath.render_json)
def json(self: Model, request: morepath.Request) -> dict[str, str]:
    return {"id": self.id}


@App.view(model=Root)
def root_default(self: Root, request: morepath.Request) -> str:
    return f"The root: {self.value}"


@App.view(model=Root, name="link")
def root_link(self: Root, request: morepath.Request) -> str:
    return request.link(self)
