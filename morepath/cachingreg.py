
class RegRegistry(object):
    """A registry to group together the implementation of delegated
    methods of one application.

    """

    factory_arguments = {'installers': list}
    # The installers pseudo-registry is a list with functions that
    # install the implementation of delegated functions on an object.

    def __init__(self, installers):
        for func in installers:
            func(self)

    def __getitem__(self, delegator):
        return getattr(self, delegator.__name__)
