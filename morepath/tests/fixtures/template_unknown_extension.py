from typing import Any

import morepath


class App(morepath.App):
    pass


@App.path(path="{name}")
class Person:
    def __init__(self, name: str):
        self.name = name


@App.html(model=Person, template="person.unknown")
def person_default(self: Person, request: morepath.Request) -> dict[str, Any]:
    return {"name": self.name}
