Static resources with Morepath
==============================

Introduction
------------

A modern client-side web application is built around JavaScript and
CSS. The code is in files that is served by the web server too.

Morepath does not include in itself a way to serve these static
resources. Instead it leaves the task to other WSGI components you can
integrate with the Morepath WSGI component. Examples of such systems
that can be integrated through WSGI are BowerStatic_, Fanstatic_ and
Webassets_.

We will focus on BowerStatic integration here. We recommend you read
its documentation, but we provide a small example of how to
integrate it here that should help you get started. You can find
all the example code in the `github repo`_.

.. _BowerStatic: http://bowerstatic.readthedocs.org

.. _Fanstatic: http://fanstatic.org

.. _Webassets: http://webassets.readthedocs.org/

.. _`github repo`: https://github.com/morepath/morepath_static

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

  class app(StaticApp):
      pass

We give it a simple HTML page on the root HTML that contains a
``<head>`` section in its HTML::


  @app.path(path='/')
  class Root(object):
      pass


  @app.html(model=Root)
  def root_default(self, request):
      return ("<!DOCTYPE html><html><head></head><body>"
              "jquery is inserted in the HTML source</body></html>")

It's important to use ``@app.html`` as opposed to ``@app.view``, as
that sets the content-header to ``text/html``, something that
BowerStatic checks before it inserts any ``<link>`` or ``<script>``
tags. It's also important to include a ``<head>`` section, as that's
where BowerStatic includes the static resources by default.

We also set up a ``main()`` function that when run serves the WSGI
application to the web::

  def main():
     morepath.autosetup()
     wsgi = app()
     morepath.run(wsgi)

All this code lives in the ``main.py`` module of a Python package.

Bower
-----

BowerStatic_ integrates the Bower_ JavaScript package manager with a
Python WSGI application such as Morepath.

Once you have ``bower`` installed, go to your Python package directory
(where the ``main.py`` lives), and install a Bower component. Let's
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
register multiple ``bower_copmonents`` directories against. Let's
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
``bower_components`` next to this module (``main.py``) in this Python
package.

Finally we need to adjust our ``main()`` function so that we plug in
the BowerStatic WSGI middleware::

  def main():
     morepath.autosetup()
     wsgi = bower.wrap(app())
     morepath.run(wsgi)

BowerStatic now lets you refer to files in the packages in
``bower_components`` to include them on the web, and also makes sure
they are available.

Saying which components to use
------------------------------

We now need to tell our application to use the ``components``
object. This causes it to look for static resources only in the
components installed there. We do this using the ``@app.static_components``
directive, like this::

  @app.static_components()
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

  @app.html(model=Root)
  def root_default(self, request):
      request.include('jquery')
      return ("<!DOCTYPE html><html><head></head><body>"
              "jquery is inserted in the HTML source</body></html>")


When we now open the view in our web browser and check its source, we
can see it includes the jquery we installed in ``bower_components``.

Note that just like the ``static_components`` directive, the
``include()`` method is not part of standard Morepath, but has been
installed by the ``more.static.StaticApp`` base class as well.


