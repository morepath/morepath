from __future__ import annotations

import dectate
import morepath


def test_cleanup() -> None:
    class App(morepath.App):
        pass

    dectate.commit(App)

    # second commit should clean up after the first one, so we
    # expect no conflict errors
    dectate.commit(App)
