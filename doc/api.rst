API
===

.. py:module:: morepath

.. autoclass:: App
  :members:

.. autoclass:: AppBase
  :members:

  .. py:method:: model(path, model=None, variables=None, base=None, get_base=None)

     Register a model for a path.

     :param path: the route for which the model is registered.
     :param model: the class of the model that the decorated function
       should return. If the directive is used on a class instead of a
       function, the model should not be provided.
     :param variables: a function that given a model object can construct
       the variables used in the path. Can be omitted if no variables
       are used in the path.
     :param base: the class of the base model from which routing
       should start.  If omitted, the routing will start from the
       mounted application's root.
     :param get_base: if a ``base`` parameter is provided, this should
       be a function that given the model can return an instance of the
       ``base``.

  .. py:method:: view(model, name='', render=None, permission=None)

    Register a view for a model.

    :param model: the class of the model for which this view is registered.
    :param name: the name of the view as it appears in the URL. If omitted,
      it is the empty string, meaning the default view for the model.
    :param render: an optional function that can render the output of the
      view function to a response, and possibly set headers such as
      ``Content-Type``, etc.
    :param permission: a permission class. The model should have this
       permission, otherwise access to this view is forbidden. If omitted,
       the view function is public.

.. autodata:: global_app

.. autofunction:: autoconfig

.. autofunction:: autosetup

.. autofunction:: setup

.. autoclass:: morepath.Request
  :members:

.. autoclass:: morepath.Response
  :members:

.. autoclass:: morepath.security.Identity
  :members:

.. autoclass:: morepath.security.BasicAuthIdentityPolicy
  :members:

.. autoclass:: Config
  :members:

.. autoclass:: morepath.config.Configurable
  :members:

.. autoclass:: morepath.config.Action
  :members:

.. autoclass:: morepath.Directive
  :members:

.. autoclass:: directive
