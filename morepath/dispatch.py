import reg
from functools import wraps, partial
from .reify import reify


class delegate(object):

    def __init__(self, *predicates):
        self.make_generic = reg.dispatch(*predicates)
        self.external_predicates = False

    def __call__(self, func):

        def install(reg):
            setattr(reg, func.__name__, self.make_generic(func))

        @wraps(func)
        @reify
        def delegator(app):
            actual = getattr(app.config.reg_registry, func.__name__)
            result = partial(actual, app)
            result.component_key_dict = actual.component_key_dict
            return result

        delegator.external_predicates = self.external_predicates
        delegator.install_delegate = install
        return delegator

    @classmethod
    def on_external_predicates(cls):
        instance = cls()
        instance.make_generic = reg.dispatch_external_predicates()
        instance.external_predicates = True
        return instance


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


def fix_signature(func):
    args = reg.arginfo(func)
    if args.args and args.args[0] == 'app':
        return func

    signature = ', '.join(
        args.args +
        (['*' + args.varargs] if args.varargs else []) +
        (['**' + args.keywords] if args.keywords else []))

    code_template = """\
def wrapper(app, {signature}):
    return _func({signature})
"""

    code_source = code_template.format(signature=signature)
    namespace = {'_func': func}
    exec(code_source, namespace)
    return namespace['wrapper']
