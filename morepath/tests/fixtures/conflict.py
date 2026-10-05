import morepath


class App(morepath.App):
    pass


@App.path(path="/")
class Root:
    pass


@App.path(path="/", model=Root)
def get_root():
    return Root()
