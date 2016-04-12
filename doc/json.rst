JSON and objects
================

Introduction
------------

Morepath lets you define a JSON representations for arbitrary Python
objects. When you return such an object from a json view, the object
is automatically converted to JSON. When JSON comes in as the POST or
PUT body of the request, this JSON can be automatically converted to a
Python object. This system allows you to write views in terms of
Python objects instead of JSON.

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

load_json
---------

The :meth:`App.load_json` directive lets you define a function that
turns incoming JSON into a Python object. We detect JSON with the
type field ``Item`` and interpret it as an ``Item`` instance, and
pass through everything else::

  @App.load_json()
  def load_json(json, request):
      if json.get('type') != 'Item':
          return json
      return Item(json['x'])

When you write a ``json`` view you automatically get the ``Item``
instance as the ``body_obj`` attribute of the ``request``::

  @App.json(model=Collection, request_method='POST')
  def collection_post(self, request):
      collection.add(request.body_obj)
      return "success!"

For a worked out example that uses ``load_json`` see :doc:`rest`.
