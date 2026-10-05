import morepath


class App(morepath.App):
    pass


@App.path(path="")
class Root:
    pass


@App.html(model=Root)
def index(self: Root, request: morepath.Request) -> str:
    return "the root"
