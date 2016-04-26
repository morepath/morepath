Static resources with Morepath
==============================

Introduction
------------

A modern client-side web application is built around JavaScript and
CSS. A web server is responsible for serving these and other types
of static content such as images to the client.

Morepath does not include in itself a way to serve these static
resources. Instead it leaves the task to other WSGI components you can
integrate with the Morepath WSGI component. Examples of such systems
that can be integrated through WSGI are BowerStatic_, Fanstatic_,
Webassets_, and webob.static_.

Examples will focus on BowerStatic integration to demonstrate a method
for serving JavaScript and CSS. To demonstrate a method for serving
other static resources such as an image we will use webob.static.

We recommend you read the BowerStatic documentation, but we provide a
small example of how to integrate it here that should help you get
started. You can find all the example code in the `github repo`_.

.. _BowerStatic: http://bowerstatic.readthedocs.org

.. _Fanstatic: http://fanstatic.org

.. _Webassets: http://webassets.readthedocs.org/

.. _`github repo`: https://github.com/morepath/morepath_static

.. _webob.static: http://webob.readthedocs.org/en/latest/modules/static.html

Application layout
------------------

To integrate BowerStatic with Morepath we can use the `more.static`_
extension.

.. _`more.static`: https://pypi.python.org/pypi/more.static

First we need to include ``more.static`` as a dependency of our code
in ``setup.py``. Once it is installed, we can create a Morepath
application that subclasses from ``more.static.StaticApp`` to get its
functionality::

  from more.static import StaticApp

  class App(StaticApp):
      pass

We give it a simple HTML page on the root HTML that contains a
``<head>`` section in its HTML::


  @App.path(path='/')
  class Root(object):
      pass


  @App.html(model=Root)
  def root_default(self, request):
      return ("<!DOCTYPE html><html><head></head><body>"
              "jquery is inserted in the HTML source</body></html>")

It's important to use ``@App.html`` as opposed to ``@App.view``, as
that sets the content-header to ``text/html``, something that
BowerStatic checks before it inserts any ``<link>`` or ``<script>``
tags. It's also important to include a ``<head>`` section, as that's
where BowerStatic includes the static resources by default.

The app configuration code we store in the ``app.py`` module of the Python
package.

In the ``run.py`` module of the Python package we set up a ``run()`` function
that when run serves the WSGI application to the web::

  from .app import App

  def run():
     morepath.autoscan()
     App.commit()
     wsgi = App()
     morepath.run(wsgi)

Manual scan
-----------

We recommend you use ``morepath.autoscan`` to make sure that all code
that uses Morepath is automatically scanned. If you *do not* use
``autoscan`` but use manual ``morepath.scan()`` instead, you need to
scan ``more.static`` explicitly, like this::

  import more.static

  def run():
     morepath.scan(more.static)
     App.commit()
     wsgi = App()
     morepath.run(wsgi)

Bower
-----

BowerStatic_ integrates the Bower_ JavaScript package manager with a
Python WSGI application such as Morepath.

Once you have ``bower`` installed, go to your Python package directory
(where the ``app.py`` lives), and install a Bower component. Let's
take ``jquery``::

  bower install jquery

You should now see a ``bower_components`` subdirectory in your Python
package. We placed it here so that when we distribute the Python
package that contains our application, the needed bower components are
automatically included in the package archive. You could place
``bower_components`` elsewhere however and manage its contents
separately.

.. _bower: http://bower.io

Registering ``bower_components``
--------------------------------

BowerStatic needs a single global ``bower`` object that you can
register multiple ``bower_components`` directories against. Let's
create it first::

  bower = bowerstatic.Bower()

We now tell that ``bower`` object about our ``bower_component``
directory::

  components = bower.components(
    'app', os.path.join(os.path.dirname(__file__), 'bower_components'))


The first argument to ``bower.components`` is the name under which we
want to publish them. We just pick ``app``. The second argument
specifies the path to the ``bower.components`` directory. The
``os.path`` business here is a way to make sure that we get the
``bower_components`` next to this module (``app.py``) in this Python
package.

BowerStatic now lets you refer to files in the packages in
``bower_components`` to include them on the web, and also makes sure
they are available.

Saying which components to use
------------------------------

We now need to tell our application to use the ``components``
object. This causes it to look for static resources only in the
components installed there. We do this using the ``@App.static_components``
directive, like this::

  @App.static_components()
  def get_static_components():
      return components

You could have another application that use another ``components``
object, or share this ``components`` with the other application. Each
app can only have a single ``components`` registered to it, though.

The ``static_components`` directive is not part of standard Morepath.
Instead it is part of the ``more.static`` extension, which we enabled
before by subclassing from ``StaticApp``.

Including stuff
---------------

Now we are ready to include static resources from ``bower_components``
into our application. We can do this using the ``include()`` method on
request. We modify our view to add an ``include()`` call::

  @App.html(model=Root)
  def root_default(self, request):
      request.include('jquery')
      return ("<!DOCTYPE html><html><head></head><body>"
              "jquery is inserted in the HTML source</body></html>")


When we now open the view in our web browser and check its source, we
can see it includes the jquery we installed in ``bower_components``.

Note that just like the ``static_components`` directive, the
``include()`` method is not part of standard Morepath, but has been
installed by the ``more.static.StaticApp`` base class as well.

Local components
----------------

In many projects we want to develop our *own* client-side JS or CSS
code, not just rely on other people's code. We can do this by using
local components. First we need to wrap the existing ``components`` in
an object that allows us to add local ones::

  local = bower.local_components('local', components)

We can now add our own local components. A local component is a directory
that needs a ``bower.json`` in it. You can create a ``bower.json`` file
most easily by going into the directory and using ``bower init`` command::

  $ mkdir my_component
  $ cd my_component
  $ bower init

You can edit the generated ``bower.json`` further, for instance to
specify dependencies. You now have a bower component. You can add any
static files you are developing into this directory.

Now you need to tell the local components object about it::

  local.component('/path/to/my_component', version=None)

See the `BowerStatic local component documentation
<http://bowerstatic.readthedocs.org/en/latest/local.html>`_ for more
of what you can do with ``version`` -- it's clever about automatically
busting the cache when you change things.

You need to tell your application that instead of plain ``components``
you want to use ``local`` instead, so we modify our
``static_components`` directive::

  @App.static_components()
  def get_static_components():
      return local

When you now use ``request.include()``, you can include local
components by their name (as in ``bower.json``) as well::

  request.include('my_component')

It automatically pulls in any dependencies declared in ``bower.json``
too.

As mentioned before, check the ``morepath_static`` `github repo`_ for
the complete example.


A note about mounted applications
---------------------------------

``more.static`` uses a tween to inject scripts into the response (see
:doc:`tweens`). If you use ``more.static`` in a view in a mounted
application, you need to make sure that the root application also
derives from ``more.static.StaticApp``, otherwise the resources aren't
inserted correctly::

  from more.static import StaticApp

  class App(StaticApp):  # this needs to subclass StaticApp too
      pass

  class Mounted(StaticApp):
      pass

   @App.mount(app=Mounted, path='mounted')
   def mount():
      return Mounted()


Other static content
--------------------

In essence, Morepath doesn't enforce any particular method for serving
static content to the client as long as the content eventually ends up
in the response object returned. Therefore, there are different
approaches to serving static content.

Since a Morepath view returns a WebOb response object, that object
can be loaded with any type of binary content in the body along
with the necessary HTTP headers to describe the content type and size.

In this example, we use a WebOb helper class webob.static.FileApp_
to serve a PNG image::

  from webob import static

  @App.path(path='')
  class Image(object):
      path = 'image.png'

  @App.view(model=Image)
  def view_image(self, request):
      return request.get_response(static.FileApp(self.path))

In the above example FileApp does the heavy lifting by opening
the file, guessing the MIME type, updating the headers, and returning
the response object which is in-turn returned by the Morepath view.
Note that the same helper class can be used to to serve most types
of ``MIME`` content.

This example is one way to serve an image, but it is not the only way.
In cases that require a more elaborate method for serving the content
this `WebOb File-Serving Example`_ may be helpful.

.. _`WebOb File-Serving Example`: http://webob.readthedocs.org/en/latest/file-example.html
.. _webob.static.FileApp: http://webob.readthedocs.org/en/latest/modules/static.html#webob.static.FileApp
