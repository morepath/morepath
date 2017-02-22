JSON and validation
===================

Introduction
------------

Morepath lets you define a JSON representations for arbitrary Python
objects. When you return such an object from a json view, the object
is automatically converted to JSON.

When JSON comes in as the POST or PUT body of the request, you can
define how it is to be converted to a Python object and how it is to
be validated.

This feature lets you plug in external (de)serialization libraries, such
as Marshmallow_. We've provided Marshmallow integration for Morepath in
`more.marshmallow`_

.. _Marshmallow: https://marshmallow.readthedocs.io/

.. _`more.marshmallow`: https://pypi.python.org/pypi/more.marshmallow

dump_json
---------

The :meth:`morepath.App.dump_json` directive lets you define a function
that turns a model of a particular class into JSON. Here we define it
for an ``Item`` class::

  class Item(object):
     def __init__(self, value):
         self.value = value

  @App.dump_json(model=Item)
  def dump_item_json(self, request):
      return { 'type': 'Item', 'x': self.value }

So for instance, ``Item('foo')`` is represented in JSON as::

  {
    'type': 'Item',
    'x': 'foo'
  }

If we omit the ``model`` argument from the directive, we define a
general dump_json function that applies to all objects.

Now we can write a JSON view that just returns an ``Item`` instance::

  @App.json(model=Item)
  def item_default(self, request):
      return self

The ``self`` we return in this view is an istance of ``Item``. This is
now automatically converted to a JSON object.

load function for views
-----------------------

When you specify the ``load`` function in a view directive you can
specify how to turn the request body for a POST or PUT method into
a Python object for that view. This Python object comes in as the
third argument to your view function::

    def my_load(request):
        return request.json

    @App.json(model=Item, request_method='POST', load=my_load)
    def item_post(self, request, obj):
       # the third obj argument contains the result of my_load(request)

The ``load`` function takes the request and must return some Python object (such
as a simple ``dict``). If the data supplied in the request body is incorrect and
cannot be converted into a Python object then you should raise an exception.
This can be a webob exception (we suggest
:class:`webob.exc.HTTPUnprocessableEntity`), but you could also define your own
custom exception and provide a view for it that sets the status to 422. This way
conversion and validation errors are reported to the end user.
