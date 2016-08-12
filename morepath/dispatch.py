import reg
from functools import wraps, partial
from . import generic
from .cachingreg import RegRegistry
from .reify import reify


def patch(obj):
    def dec(func):
        setattr(obj, func.__name__, func)
        return func
    return dec


class delegate(object):

    name_map = dict(
        get_view='view',
    )

    def __init__(self, *predicates):
        self.make_generic = reg.dispatch(*predicates)

    def __call__(self, func):
        generic_name = func.__name__
        scope = RegRegistry

        if not hasattr(scope, generic_name):
            delegate = self.make_generic(func)
            delegate.needs_signature_fix = True

            if generic_name in self.name_map:
                setattr(generic, self.name_map[generic_name], delegate)

            @reify
            def setup(reg):
                @patch(delegate)
                def register(impl, **kw):
                    reg.register_function(delegate, impl, **kw)

                @patch(delegate)
                def key_dict_to_predicate_key(key_dict):
                    return reg.key_dict_to_predicate_key(
                        delegate.wrapped_func,
                        key_dict)

                return delegate

            setattr(scope, generic_name, setup)

        @reify
        @wraps(func)
        def delegator(self, *args, **kw):
            actual = getattr(self.config.reg_registry, generic_name)
            result = partial(actual, self, lookup=self.lookup)

            @patch(result)
            def component_key_dict(**predicates):
                return actual.component_key_dict(
                    lookup=self.lookup, **predicates)

            return result

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
