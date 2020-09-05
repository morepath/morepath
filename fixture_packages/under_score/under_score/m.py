import morepath


class UnderscoreApp(morepath.App):
    pass


class Bar:
    pass


@UnderscoreApp.path(path="bar", model=Bar)
def get_bar():
    return Bar()
