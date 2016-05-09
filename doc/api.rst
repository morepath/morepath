API
===

``morepath``
------------

.. automodule:: morepath

.. autoclass:: App
  :members:
  :special-members:

.. autofunction:: scan

.. autofunction:: autoscan

.. autofunction:: commit

.. autofunction:: run

.. autofunction:: settings()

.. autoclass:: Request
  :members:

.. autoclass:: Response
  :members:

.. autofunction:: render_html

.. autofunction:: render_json

.. autofunction:: redirect

.. autoclass:: morepath.Identity
  :members:

.. autofunction:: morepath.remember_identity(response, request, identity)

.. autofunction:: morepath.forget_identity(response, request)

.. autoclass:: morepath.IdentityPolicy
  :members:

.. autodata:: morepath.NO_IDENTITY

.. autodata:: morepath.EXCVIEW

.. autodata:: morepath.HOST_HEADER_PROTECTION

.. autoclass:: morepath.Converter
  :members:

.. autofunction:: morepath.enable_implicit

.. autofunction:: morepath.disable_implicit

``morepath.error`` -- exception classes
---------------------------------------

.. automodule:: morepath.error

Morepath specific errors:

.. autoexception:: morepath.error.AutoImportError

.. autoexception:: morepath.error.TrajectError

.. autoexception:: morepath.error.LinkError

.. autoexception:: morepath.error.TopologicalSortError

``morepath.pdbsupport`` -- debugging support
--------------------------------------------

.. automodule:: morepath.pdbsupport

.. autofunction:: morepath.pdbsupport.set_trace
