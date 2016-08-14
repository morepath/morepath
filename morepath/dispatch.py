import reg
from functools import wraps, partial
from .reify import reify


def patch(obj):
    def dec(func):
        setattr(obj, func.__name__, func)
        return func
    return dec


class delegate(object):

    def __init__(self, *predicates):
        self.make_generic = reg.dispatch(*predicates)

    def __call__(self, func):
        delegate = self.make_generic(func)

        def install(reg):
            # It is currently assumed that reg is an instance of
            # RegRegistry.

            @patch(delegate)
            def register(impl, **kw):
                reg.register_function(delegate, impl, **kw)

            @patch(delegate)
            def key_dict_to_predicate_key(key_dict):
                return reg.key_dict_to_predicate_key(
                    delegate.wrapped_func,
                    key_dict)

            @patch(delegate)
            def register_external_predicates(predicates):
                reg.register_external_predicates(delegate, predicates)
                reg.register_dispatch(delegate)

            setattr(reg, func.__name__, delegate)

        @wraps(func)
        @reify
        def delegator(app):
            actual = getattr(app.config.reg_registry, func.__name__)
            lookup = app.config.reg_registry.caching_lookup
            result = partial(actual, app, lookup=lookup)
            result.component_key_dict = partial(
                actual.component_key_dict, lookup=lookup)

            return result

        delegator.external_predicates = delegate.external_predicates
        delegator.install_delegate = install
        return delegator

    @classmethod
    def on_external_predicates(cls):
        instance = cls()
        instance.make_generic = reg.dispatch_external_predicates()
        return instance


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
