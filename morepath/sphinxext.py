"""Sphinx extension to make sure directives have proper signatures.

This is tricky as directives are added as methods to the ``AppBase``
object using the directive decorator, and the signature needs to be
obtained from the directive class's ``__init__`` manually. In addition
this signature has a first argument (``app``) that needs to be
removed.
"""
import inspect

# def process_signature(app, what, name, obj, options, signature,
#                       return_annotation):
#     actual_directive = getattr(obj, 'actual_directive', None)
#     if actual_directive is None:
#         return signature, return_annotation
#     from sphinx.ext.autodoc import Documenter  # inline to let scanning work
#     documenter = Documenter('dummy', 'dummy')
#     documenter.object = actual_directive
#     signature = documenter.format_signature()
#     return (signature, return_annotation)

def setup(app):
    # all inline to avoid dependency on sphinx.ext.autodoc which
    # would trip up scanning
    from sphinx.ext.autodoc import ModuleDocumenter, MethodDocumenter

    class DirectiveDocumenter(MethodDocumenter):
        objtype = 'morepath_directive'

        priority = 1

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
            return True

        def format_signature(self):
            result = super(DirectiveDocumenter, self).format_signature()
            # brute force ripping out of first argument
            result = result.replace('(app, ', '(')
            result = result.replace('(base_app, ', '(')
            result = result.replace('(app)', '()')
            return result

    app.add_autodocumenter(DirectiveDocumenter)
