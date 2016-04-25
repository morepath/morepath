Superpowers
===========

We said Morepath has super powers. Are they hard to use, then? No:
they're both powerful and also easy to use, which makes them even
more super!

.. _easy-linking:

Link with Ease
--------------

Since Morepath knows about your models, it can generate links to them. If
you have a model instance (for example through a database query), you
can get a link to it by calling :meth:`morepath.Request.link`::

  request.link(my_obj)

Want a link to its edit view (or whatever named view you want)? Just
do::

  request.link(my_obj, 'edit')

If you create links this way everywhere (and why shouldn't you?), you
know your application's links will never break.

For much more, see :doc:`paths_and_linking`.

.. _generic-ui:

Generic UI
----------

Morepath knows about model inheritance. It lets you define views for a
base class that automatically become available for all
subclasses. This is a powerful mechanism to let you write generic UIs.

For example, if we have this generic base class::

  class ContainerBase(object):
      def entries(self):
         """All entries in the container returned as a list."""

We can easily define a generic default view that works for all
subclasses::

  @App.view(model=ContainerBase)
  def overview(self, request):
      return ', '.join([entry.title for entry in self.entries()])

But what if you want to do something different for a particular
subclass? What if ``MySpecialContainer`` needs it own custom default
view? Easy::

  @App.view(model=MySpecialContainer)
  def special_overview(self, request):
      return "A special overview!"

Morepath leverages the power of the flexible Reg_ generic function
library to accomplish this.

For much more, see :doc:`views`.

.. _Reg: http://reg.readthedocs.org

.. _model-driven-permissions:

Model-driven Permissions
------------------------

Morepath features a very flexible but easy to use permission system.
Let's say we have an ``Edit`` permission; it's just a class::

  class Edit(object):
      pass

And we have a view for some ``Document`` class that we only want to be
accessible if the user has an edit permission::

  @App.view(model=Document, permission=Edit)
  def edit_document(self, request):
      return "Editable"

How does Morepath know whether someone has ``Edit`` permission? We
need to tell it using the :meth:`morepath.App.permission_rule`
directive. We can implement any rule we want, for instance this one::

  @App.permission_rule(model=Document, permission=Edit)
  def have_edit_permission(identity, model, permission):
      return model.has_permission(identity.userid)

Instead of a specific rule that only works for ``Document``, we can
also give our app a broad rule (use ``model=object``).

.. _composable-views:

Composable Views
----------------

Let's say you have a JSON view for a ``Document`` class::

  @App.json(model=Document)
  def document_json(self, request):
      return {'title': self.title}

And now we have a view for a container that contains documents. We want
to automatically render the JSON views of the documents in a list. We
can write this::

  @App.json(model=DocumentContainer)
  def document_container_json(self, request):
      return [document_json(request, doc) for doc in self.entries()]

Here we've used ``document_json`` ourselves. But what now if the
container does not only contain ``Document`` instances? What if one of
them is a ``SpecialDocument``? Our ``document_container_json``
function breaks. How to fix it? Easy, we can use
:meth:`morepath.Request.view`::

  @App.json(model=DocumentContainer)
  def document_container_json(self, request):
      return [request.view(doc) for doc in self.entries()]

Now ``document_container_json`` works for anything in the container
model that has a default view!

.. _extensible-apps:

Extensible Applications
-----------------------

Somebody else has written an application with Morepath. It contains lots
of stuff that does exactly what you want, and one view that *doesn't*
do what you want::

  @App.view(model=Document)
  def recalcitrant_view(self, request):
      return "The wrong thing!"

Ugh! We can't just change the application as it needs to continue to
work in its original form. Besides, it's being maintained by someone
else. What do we do now? Monkey-patch? Not at all: Morepath got you
covered. You simply create a new application subclass that extends the
original::

  class MyApp(App):
      pass

We now have an application that does exactly what ``app`` does. Now
to override that one view to do what we want::

  @MyApp.view(model=Document)
  def whatwewant(self, request):
      return "The right thing!"

And we're done!

It's not just the view directive that works this way: *all* Morepath
directives work this way.

Morepath also lets you mount one application within another, allowing
composition-based reuse. See :doc:`app_reuse` for more
information. Using these techniques you can build large applications,
see :doc:`building_large_applications`.

.. _extensible-framework:

Extensible Framework
--------------------

Morepath's directives are implemented using Dectate_, the
meta-framework for configuring Python frameworks. You can define new
directives and registries for Morepath with ease::

  class Extended(morepath.App):
      pass

  @Extended.directive('widget')
  class WidgetAction(dectate.Action):
      config = {
          'widget_registry': dict  # use dict as a registry
      }
      def __init__(self, name):
          self.name = name

       def identifier(self):
          return self.name

       def perform(self, obj, widget_registry):
          widget_registry[self.name] = obj

  @Extended.widget('input')
  def input_widget():
      ...

  @Extended.widget('label')
  def label_widget():
      ...

.. _Dectate: http://dectate.readthedocs.org
