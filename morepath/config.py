from copy import copy
import venusian
import sys

class Action(object):
    def discriminator(self):
        """Returns an immutable that uniquely identifies this config.

        Used for configuration conflict detection.
        """
        raise NotImplementedError()

    # XXX needs docs
    def clone(self):
        return copy(self)

    def prepare(self, obj):
        """Prepare action for configuration.

        obj - the object being registered
        """
        pass

    def perform(self, obj):
        """Register whatever is being configured.

        obj - the object being registered
        """
        raise NotImplementedError()


class Directive(Action):
    def __call__(self, wrapped):
        def callback(scanner, name, obj):
            scanner.config.action(self, obj)
        venusian.attach(wrapped, callback)
        return wrapped


class Config(object):
    def __init__(self):
        self.actions = []

    def scan(self, package=None, ignore=None):
        if package is None:
            package = caller_package()
        scanner = venusian.Scanner(config=self)
        scanner.scan(package, ignore=ignore)

    def action(self, action, obj):
        self.actions.append((action, obj))

    def validate(self):
        # XXX check for conflicts
        # XXX check that all base of an app is another app,
        # can only do this in the end
        # XXX a model cannot be registered multiple times in the same
        # registry. same for app
        # XXX check that a model registration that has a base that is
        # not an app supplies a get_base
        pass

    def commit(self):
        actions = []
        for action, obj in self.actions:
            action = action.clone()  # so that prepare starts fresh
            action.prepare(obj)
            actions.append((action, obj))

        for action, obj in actions:
            action.perform(obj)

    # XXX consider a load() that does scan & commit

# taken from pyramid.path
def caller_module(level=2, sys=sys):
    module_globals = sys._getframe(level).f_globals
    module_name = module_globals.get('__name__') or '__main__'
    module = sys.modules[module_name]
    return module


def caller_package(level=2, caller_module=caller_module):
    # caller_module in arglist for tests
    module = caller_module(level+1)
    f = getattr(module, '__file__', '')
    if (('__init__.py' in f) or ('__init__$py' in f)): # empty at >>>
        # Module is a package
        return module
    # Go up one level to get package
    package_name = module.__name__.rsplit('.', 1)[0]
    return sys.modules[package_name]
