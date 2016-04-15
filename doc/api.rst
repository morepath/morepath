API
===

``morepath``
------------

.. py:module:: morepath

.. autoclass:: App
  :members:
  :special-members:

.. autofunction:: scan

.. autofunction:: autoscan

.. autofunction:: autosetup

.. autofunction:: commit

.. autofunction:: autocommit

.. autofunction:: run

.. autofunction:: settings

.. autofunction:: redirect

.. autoclass:: Request
  :members:

.. autoclass:: Response
  :members:

.. autofunction:: render_html

.. autofunction:: render_json

.. autoclass:: morepath.Identity
  :members:

.. autofunction:: morepath.remember_identity

.. autofunction:: morepath.forget_identity

.. autoclass:: morepath.IdentityPolicy
  :members:

.. autoclass:: morepath.security.BasicAuthIdentityPolicy
  :members:

.. autodata:: morepath.NO_IDENTITY

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
