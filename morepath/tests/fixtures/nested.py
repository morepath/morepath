import morepath


class Outer_app(morepath.App):
    pass


class App(morepath.App):
    pass


@Outer_app.mount("inner", App)
def inner_context() -> App:
    return App()


App.path(path="")


class Root:
    pass


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
