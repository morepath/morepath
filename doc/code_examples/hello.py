import morepath


class App(morepath.App):
    pass


@App.path(path="")
class Root:
    pass


@App.view(model=Root)
def hello_world(self: Root, request: morepath.Request) -> str:
    return "Hello world!"


if __name__ == "__main__":
    morepath.run(App())
