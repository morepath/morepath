"""Sphinx extension to make sure directives have proper signatures.

This is tricky as directives are added as methods to the ``App``
object using the directive decorator, and the signature needs to be
obtained from the directive class's ``__init__`` manually. In addition
this signature has a first argument (``app``) that needs to be
removed.
"""
import inspect


def setup(app):  # pragma: nocoverage
    # all inline to avoid dependency on sphinx.ext.autodoc which
    # would trip up scanning
    from sphinx.ext.autodoc import ModuleDocumenter, MethodDocumenter

    class DirectiveDocumenter(MethodDocumenter):
        objtype = 'morepath_directive'
        priority = MethodDocumenter.priority + 1
        member_order = 49

        @classmethod
        def can_document_member(cls, member, membername, isattr, parent):
            return (inspect.isroutine(member) and
                    not isinstance(parent, ModuleDocumenter) and
                    hasattr(member, 'actual_directive'))

        def import_object(self):
            if not super(DirectiveDocumenter, self).import_object():
                return
            object = getattr(self.object, 'actual_directive', None)
            if object is None:
                return False
            self.object = object.__init__
            self.directivetype = 'decorator'
            return True

        def format_signature(self):
            result = super(DirectiveDocumenter, self).format_signature()
            # brute force ripping out of first argument
            result = result.replace('(app, ', '(')
            result = result.replace('(base_app, ', '(')
            result = result.replace('(app)', '()')
            return result

    def decide_to_skip(app, what, name, obj, skip, options):
        if what != 'class':
            return skip
        directive = getattr(obj, 'actual_directive', None)
        if directive is not None:
            return False
        return skip

    app.connect('autodoc-skip-member', decide_to_skip)
    app.add_autodocumenter(DirectiveDocumenter)
