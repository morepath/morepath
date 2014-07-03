from reg import implicit

_implicit_enabled = True


def set_implicit(lookup):
    if _implicit_enabled:
        implicit.lookup = lookup


def enable_implicit():
    global _implicit_enabled
    _implicit_enabled = True


def disable_implicit():
    global _implicit_enabled
    _implicit_enabled = False
