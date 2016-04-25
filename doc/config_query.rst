Querying configuration
======================

Creating a tool
---------------

A Morepath-based application may over time grow big, have multiple
authors and spread over many modules. In this case it is helpful to
have a tool that helps you explore Morepath configuration and quickly
find what directives are defined where. The Dectate_ library
:ref:`details how to create such a tool <dectate:query_tool>`, but we
repeat it here for Morepath::

  import dectate
  from mybigapp import App

  def query_tool():
      dectate.query_tool(App.commit())

You save it in a module called ``query.py`` in the ``mybigapp``
package. Then you hook it up in ``setup.py`` so that a query script
gets generated::

  entry_points={
      'console_scripts': [
          'morepathq = mybigapp.query:query_tool',
      ]
  },

Now when you re-install your project, you get a command-line query
tool called ``morepathq`` that lets you issue queries.

What just happened?

* In order to be able to query an app's configuration you need to
  commit it first. ``App.commit()`` also commits any other application
  you may have mounted into it. You get an iterable of apps that got
  committed.

* You pass this iterable into the ``query_tool`` function. This lets
  the query tool search through the configuration of the apps you
  committed only.

* You hook it up so that a command-line script gets generated using
   setuptool's ``console_scripts`` mechanism.

.. _Dectate: http://dectate.readthedocs.org

Usage
-----

So now that you have a ``morepathq`` query tool, let's use it:

.. code-block:: console

  $ morepathq view
  App: <class 'mybigapp.App'>
    File ".../somemodule.py", line 4
    @App.html(model=Foo)

    File ".../anothermodule.py", line 8
    @App.json(model=Bar)

Here we query for the ``view`` directive; since the ``view`` directive
is grouped with ``json`` and ``html`` we get those back too. We get
the module and line number where the directive was used.

You can also filter:

.. code-block:: console

  $ morepathq view model=mybigapp.model.Foo
  App: <class 'mybigapp.App'>
    File ".../somemodule.py", line 4
    @App.html(model=Foo)

Here we query all views that have the ``model`` value set to ``Foo``
or one of its subclasses. Note that in able to refer to ``Foo`` in the
query we use the dotted name to that class in the module it was
defined.

You can query any Morepath directive this way:

.. code-block:: console

  $ morepathq path model=mybigapp.model.Foo
  App: <class 'mybigapp.App'>
    File ".../path.py", line 8
    @App.path(model=Foo, path="/foo")

