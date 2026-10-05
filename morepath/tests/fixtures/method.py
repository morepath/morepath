import morepath


class App(morepath.App):
    pass


class StaticMethod:
    pass


class Root:
    def __init__(self) -> None:
        self.value = "ROOT"

    @staticmethod
    @App.path(model=StaticMethod, path="static")
    def static_method() -> StaticMethod:
        return StaticMethod()


@App.view(model=StaticMethod)
def static_method_default(self: StaticMethod, request: morepath.Request) -> str:
    return "Static Method"
