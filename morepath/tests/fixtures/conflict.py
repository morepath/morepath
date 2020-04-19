import morepath


class app(morepath.App):
    pass


@app.path(path="/")
class Root:
    pass


@app.path(path="/", model=Root)
def get_root():
    return Root()
