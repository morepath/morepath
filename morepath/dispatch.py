import reg
from functools import wraps, partial
from .reify import reify


class delegate(object):
    """Decorate a :class:`morepath.App` method that delegates its
    implementation to functions decorated by some app directive.

    The optional predicates specify that the method does multiple
    dispatching, on what arguments, and how.
    """

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
        """Specify that the method is to be implemented by a generic function
        with external predicates."""
        instance = cls()
        instance.make_generic = reg.dispatch_external_predicates()
        instance.external_predicates = True
        return instance


class RegRegistry(object):
    """A registry to group together the implementation of delegated
    methods of one application.

    """

    app_class_arg = True

    def __init__(self, app_class):
        for name in dir(app_class):
            func = getattr(getattr(app_class, name), 'install_delegate', None)
            if func is not None:
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
