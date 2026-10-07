import morepath


class App(morepath.App):
    pass


class Model:
    def __init__(self, id: str) -> None:
        self.id = id


@App.path(model=Model, path="{id}")
def get_model(id: str) -> Model:
    return Model(id)


with App.view(model=Model) as view:

    @view()
    def default(self: Model, request: morepath.Request) -> str:
        return f"Default view: {self.id}"

    @view(name="edit")
    def edit(self: Model, request: morepath.Request) -> str:
        return f"Edit view: {self.id}"
