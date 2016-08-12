import reg
from functools import wraps
from . import generic


class delegate(object):

    name_map = dict(
        _get_class_path='class_path',
        _get_path_variables='path_variables',
        _get_default_path_variables='default_path_variables',
        _get_deferred_link_app='deferred_link_app',
        _get_deferred_class_link_app='deferred_class_link_app',
        do_verify_identity='verify_identity',
        permits='permits',
        do_load_json='load_json',
        do_dump_json='dump_json',
        _get_link_prefix='link_prefix',
        get_view='view',
    )

    def __init__(self, *predicates):
        self.make_generic = reg.dispatch(*predicates)

    def __call__(self, func):
        generic_name = self.name_map[func.__name__]

        if not hasattr(generic, generic_name):
            generic_func = self.make_generic(func)
            setattr(generic, generic_name, generic_func)
            generic_func.needs_signature_fix = True

        @wraps(func)
        def delegator(self, *args, **kw):
            return getattr(generic, generic_name)(
                self, lookup=self.lookup, *args, **kw)

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
