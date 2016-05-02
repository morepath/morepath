App Reuse
=========

Morepath is a microframework with a difference: it's small and easy to
learn like the others, but has special super powers under the hood.

One of those super powers is Reg_, which along with Morepath's
model/view separation makes it easy to write reusable views. But here
we'll talk about another super power: Morepath's application reuse
facilities.

We'll talk about how Morepath lets you isolate applications, extend
and override applications, and compose applications together. Morepath
makes this not only possible, but also *simple*.

Other web frameworks have mechanisms for overriding behavior and
reusing code. But these were typically added in an ad-hoc fashion as
new needs arose.

Morepath instead has *general* mechanisms for app extension and
reuse. Any normal Morepath app is reusable without extra
effort. Anything registered in a Morepath app can be overridden.

.. _Reg: http://blog.startifact.com/posts/reg-now-with-more-generic.html

Application Isolation
---------------------

Morepath lets you create app classes like this:

.. code-block:: python

  class App(morepath.App):
      pass

When you instantiate the app class, you get a WSGI application. The
app class itself serves as a registry for application construction
information. You specify this configuration with decorators. Apps
consist of paths and views for models:

.. code-block:: python

  @App.path(model=User, path='users/{username}')
  def get_user(username):
      return query_for_user(username)

  @App.view(model=User)
  def render_user(self, request):
      return "User: %s" % self.username

Here we've exposed the ``User`` model class under the path
``/users/{username}``. When you go to such a URL, Morepath looks up
the default (unnamed) view. We've implemented that too: it renders
"User: {username}".

What now if we have another app where we want to publish ``User`` in a
different way? No problem, we can create one:

.. code-block:: python

  class OtherApp(morepath.App):
      pass

  @OtherApp.path(model=User, path='different_path/{username}')
  def get_user(username):
      return different_query_for_user(username)

  @OtherApp.view(model=User)
  def render_user(self, request):
      return "Differently Displayed User: %s" % self.username

Here we expose ``User`` to the web again, but use a different path and
a different view. If you use ``OtherApp`` (even in the same runtime), it
functions independently from ``App``.

App isolation is nothing special in Morepath; it's obvious that this
is possible. But that's what we wanted. Let's look at some other
features next.

Application Extension
---------------------

Let's look at our first application ``App`` again. It exposes a single
view for users (the default view). What now if we want to add a new
functionality to this application so that we can edit users as well?

This is simple; we can add a new ``edit`` view to ``App``:

.. code-block:: python

  @App.view(model=User, name='edit')
  def edit_user(self, request):
      return 'Edit user: %s' % self.username

The string we return here is of course useless for a *real* edit view,
but you get the idea.

But what if we have a scenario where there is a core application and
we want to extend it *without modifying it*?

Why would this ever happen, you may ask? In complex applications and
reuse scenarios it does. Imagine you have a common application core
and you want to be able to plug into it. Meanwhile, you want that core
application to still function as before when used (or tested!) by
itself. Perhaps there's somebody else who has created another
extension of it.

In software engineering we call this architectural principle the
`Open/Closed Principle`_, and Morepath makes it easy to follow
it. What you do is create another app that subclasses the original:

.. code-block:: python

  class ExtendedApp(App):
      pass

And then we can add the view to the extended app:

.. code-block:: python

  @ExtendedApp.view(model=User, name='edit')
  def edit_user(self, request):
      return 'Edit user: %s' % self.username

Now when we publish ``ExtendedApp`` using WSGI, the new ``edit`` view
is there, but when we publish ``App`` it won't be.

Subclassing. Obvious, perhaps. Good! Let's move on.

.. _`Open/Closed Principle`: https://en.wikipedia.org/wiki/Open/closed_principle

Application Overrides
---------------------

Now we get to a more exciting example: overriding applications. What
if instead of adding an extension to a core application you want to
override part of it? For instance, what if we want to change the
default view for ``User``?

Here's how we can do that:

.. code-block:: python

  @ExtendedApp.view(model=User)
  def render_user_differently(self, request):
      return 'Different view for user: %s' % self.username

We've now overridden the default view for ``User`` to a new view that
renders it differently.

We can also do this for model paths. Here we return a different user
object altogether in our overriding app:

.. code-block:: python

  @ExtendedApp.path(model=OtherUser, path='users/{username}')
  def get_user_differently(username):
      return OtherUser(username)

To publish ``OtherUser`` under ``/users/{username}`` it either needs
to be a subclass of ``User``. We've already registered a default view
for that class. We can also register a new default view for
``OtherUser``.

Overriding apps actually doesn't look much different from how you
build apps in the first place. Again, it's just subclassing. Hopefully
this isn't getting boring, so let's talk about something new.

Nesting Applications
--------------------

Let's talk about application composition: nesting one app in another.

Imagine our user app allows users to have a wiki associated with them.
It has paths like ``/users/faassen/wiki/my_wiki_page`` and
``/users/bob/wiki/page_on_things``.

We could implement this directly in the user app along these lines:

.. code-block:: python

  def wiki_for_user(username):
      wiki_id = get_wiki_id_for_username(username)
      return get_wiki(wiki_id)

  @App.path(model=WikiPage, path='users/{username}/wiki/{page_id}')
  def get_wiki_page(username, page_id):
      return wiki_for_user(username).get_page(page_id)

  @App.view(model=WikiPage)
  def wiki_page_default(self, request):
      return "Wiki Page"

To understand this app, we need to describe a hypothetical ``Wiki``
class first. We can get an instance of it from some database by using
``get_wiki`` with a wiki id. It has a ``get_page`` method for getting
access to wiki page objects (class ``WikiPage``). We also have a way
to determine the wiki id for a given username,
``get_wiki_id_for_username``.

This application makes available wiki pages on a sub-URL for users,
and then supplies a default view for them so we see something when we
go to the page.

There are some issues with this implementation, though:

* Why would we implement a wiki as part of our user app? Our wiki
  application should really be an app by itself, that we can use by
  itself and also test by itself.

* The ``username`` appears in the path for the ``WikiPage`` model. The
  same would apply to any other wiki related models (like the wiki
  root). Why should we have to care about the username of a user when
  we expose a wiki page?

* Related to this, what if we wanted to associate a wiki app with some
  other object such as a *project*, instead of a user? It would be
  nice if we can use the wiki app in such other contexts as well, not
  just for users.

To deal with those issues, we can create a separate app for wikis that
is only about wikis. So let's do it. Here's the wiki app by itself:

.. code-block:: python

  class WikiApp(morepath.App):
      def __init__(self, wiki_id):
          self.wiki_id = wiki_id

  @WikiApp.path(path='{page_id}', model=WikiPage)
  def get_wiki(page_id, app):
      return get_wiki(app.wiki_id).get_page(page_id)

  @WikiApp.view(model=WikiPage)
  def wiki_page_default(self, request):
      return "Wiki Page"

Here we have a stand-alone wiki app. It needs a ``wiki_id`` to be
instantiated:

.. code-block:: python

  app = WikiApp(3)

We could now use ``app`` as a WSGI application, but that only works
for one wiki id at the time. What if we want to associate the wiki
with a user like we had before? We can accomplish this by *mounting*
the wiki app into the user app, like this:

.. code-block:: python

  def variables(app):
      return dict(username=get_username_for_wiki_id(app.wiki_id))

  @App.mount(app=WikiApp, path='users/{username}/wiki',
             variables=variables)
  def mount_wiki(username):
      return WikiApp(get_wiki_id_for_username(username))

Note that in order to be able to link to ``WikiApp`` we need to supply
a special ``variables`` function that takes the wiki app and returns
the username for it. For more details, see the documentation for the
:meth:`morepath.App.mount` directive.

Linking to other mounted apps
-----------------------------

.. sidebar:: Reusing views from other applications

  Just like :meth:`morepath.Request.link`,
  :meth:`morepath.Request.view` also takes an ``app`` parameter. This
  allows you to reuse a view from another application.

Now that we have applications mounted into each other, we want a way
to make links between them.

It is easy to make a link to an object in the same application. We use
:meth:`morepath.Request.link`:

.. code-block:: python

   wiki_page = get_wiki(3).get_page('my_page')

   request.link(wiki_page)

This works to create links to wiki pages from within the wiki app. But
what if we want to link to a wiki page from *outside* the wiki app,
for instance from the user app?

To do this, we need not only the wiki page, but also a reference to
the specific mounted application the wiki page is in. We can get this
by navigating to it from the user app.

If we are in the user application, we can navigate to the mounted wiki
app using the :meth:`morepath.App.child` method:

.. code-block:: python

  wiki_app = request.app.child(WikiApp(3))

What if we want to navigate with the ``username`` under which it was
mounted instead? We can do this too. We give ``child`` the ``WikiApp``
class and then the ``username`` as a keyword argument:

.. code-block:: python

  wiki_app = request.app.child(WikiApp, username='faassen')

There is one more alternative. We can also refer to ``WikiApp`` with
the name under which it was mounted (the ``path`` by default):

.. code-block:: python

  wiki_app = request.app.child('users/{username}/wiki', username='faassen')

We can now use ``wiki_app`` to make the link from the username app to
a wiki page in the wiki app:

.. code-block:: python

   request.link(wiki_page, app=wiki_app)

What if we wanted to create a link from the wiki app into the user app
in which it was mounted? We get to the user app from the wiki app with
:attr:`morepath.App.parent`:

.. code-block:: python

  request.link(User('faassen'), app=request.app.parent)

For a quick navigation to a sibling app, there is also
:meth:`morepath.App.sibling`. To quickly get to the root app, use
:attr:`morepath.App.root`. You can also combine ``parent`` and
``child`` together to navigate the application tree.

Deferring links and views
-------------------------

If we have a lot of code that links to objects in another app, it can
get cumbersome to have to add the ``app`` parameter whenever we want
to create a view. Instead, we can declare this centrally with the
:meth:`morepath.App.defer_links` directive.

We can for instance declare for the ``WikiApp`` that to link to a
``User`` object we always use the parent app we were mounted in:

.. code-block:: python

   @WikiApp.defer_links(model=User)
   def defer_user(app, obj):
      return app.parent

You can also use it to defer to a child app. If the ``WikiPage`` model
provides a way to obtain the ``wiki_id`` for it, we can use that
information to determine what mounted ``WikiApp`` we need to link to:

.. code-block:: python

   @App.defer_links(model=WikiPage)
   def defer_wiki_page(app, obj):
      return app.child(WikiApp(obj.wiki_id))

You can defer links across multiple applications -- a wiki app may
defer objects it does not know how to link to to the app it is mounted
to, and then this app could defer to another sub-app. When creating a
link Morepath follows the defers to the application that knows how to
do it.

The :meth:`morepath.App.defer_links` directive also affects the
behavior of :meth:`morepath.Request.view` in the same way. It does
however *not* affect :meth:`morepath.Request.class_link`, as without
the instance, insufficient information is available to defer the link.

Further reading
---------------

To see an extended example of how you can structure larger
applications to support reuse, see :doc:`building_large_applications`.
