Configuration
=============

Introduction
------------

When you use a Morepath directive, for example to define a :doc:`view
<views>`, a :doc:`path <paths_and_linking>`, a :doc:`setting
<settings>` or a :doc:`tween <tweens>`, this is called Morepath
*configuration*. Morepath configuration can also be part of
third-party code you want to use.

How it works
------------

Morepath needs to be configured before it is run. That means that you
need to run the necessary configuration steps before you pass a new
instance of your application to your WSGI server::

  if __name__ == '__main__':
      morepath.autocommit()

      application = App()
      morepath.run(application)

Morepath registers any directive you used in modules that you have
imported, directly or indirectly, with the :class:`App` subclass you
used it on. It also creates a list of your app classes (:class:`App`
subclasses) you have imported.

:func:`morepath.autocommit` then commits the configuration for all of
your app classes. After this, the application can be run. The commit
procedure makes sure there are no conflicting pieces of configuration
and resolves any configuration overrides.

When you depend on a package that contains Morepath code it is
convenient to be able to scan all of it at once. That way you can't
accidentally forget to import a module and thus have its directives
not be active. You can scan a whole package with
:func:`morepath.scan`::

  import my_package

  if __name__ == '__main__':
      morepath.scan(my_package)
      morepath.autocommit()

      application = App()
      morepath.run(application)

Since scanning the current package is common, we have a convenience
shortcut that scan the package the code is in automatically. You use
it by calling :func:`morepath.scan` without arguments::

  if __name__ == '__main__':
      morepath.scan()
      morepath.autocommit()

      application = App()
      morepath.run(application)

You can also use :func:`scan` with packages that contain third-party
Morepath code, but there is actually a better way.

Scanning dependencies
---------------------

Morepath is a micro-framework at its core, but you can expand it with
other packages that add extra functionality. For instance, you can use
`more.chameleon <https://github.com/morepath/more.chameleon>`_ for
templating or `more.transaction
<https://github.com/morepath/more.transaction>`_ for SQLAlchemy
integration.

These packages contain their own Morepath configuration, so when we
use these packages we need to make sure to scan them too.

Manual scan
~~~~~~~~~~~

The most explicit way of scanning your dependencies is a manual scan.

Say you depend on `more.jinja2 <https://github.com/morepath/more.jinja2>`_
and you want to extend the the first example.

This is what you do::

  import more.jinja2

  if __name__ == '__main__':
      morepath.scan(more.jinja2) # scan Jinja2 package
      morepath.scan() # scan this package
      morepath.autocommit()

      application = App()
      morepath.run(application)

As you can see, you need to import your dependency and scan it using
:func:`scan`. If you have more dependencies, just add them in this
fashion.

Automatic scan
~~~~~~~~~~~~~~

.. sidebar:: Scanning versus activation

  Automatically configuring all packages that have Morepath
  configuration in them may seem too aggressive: what if you don't
  want to use this configuration? This is not a problem as Morepath
  makes a distinction between scanned configuration and activated
  configuration.

  Configuration is only activated if it's on the :class:`morepath.App`
  subclass you actually run as a WSGI app, or on any app class that
  your application class inherits from. App classes that you don't use
  are not active. It is therefore safe for Morepath to just scan
  everything that is available.

Manual scanning can get tedious and error-prone as you need to add
each and every new dependency that you rely on.

You can use :func:`autoscan` instead, which scans all
packages that have a dependency on Morepath declared. Let's look at a
modified example that uses ``autoscan``::

  if __name__ == '__main__':
      morepath.autoscan()
      morepath.scan()
      morepath.autocommit()

      application = App()
      morepath.run(application)

As you can see, we also don't need to import or scan dependencies
anymore. We still need to run :func:`scan` without parameters
however, so our own package or module gets scanned.

We can get rid of the :func:`scan` line if we move our own code into a
proper Python project too.

Autosetup
~~~~~~~~~

In the previous example we still needed to scan the startup module
itself, so that is why we need :func:`scan`. We can get rid of that
line by turning the code into a full Python project with its own
``setup.py``. The ``setup.py`` looks like this::

  setup(name='myapp',
        packages=find_packages(),
        install_requires=[
           'morepath'
        ])

with the code in a Python package called ``myapp`` (a directory
with an ``__init__.py`` file in it).

See :doc:`organizing_your_project` for a lot more information on how
to do this, including tips on how to best organize your Python code.

Once you put your code in a Python project with a ``setup.py``, you can
simplify the configuration scan to this::

  if __name__ == '__main__':
      morepath.autosetup()
      morepath.run(App())

:func:`morepath.autosetup()` makes sure to scan all packages with Morepath
code, and commits the configuration.

Writing scannable packages
~~~~~~~~~~~~~~~~~~~~~~~~~~

A Morepath scannable Python package has to fulfill a few requirements.

1. The package must be made available using a ``setup.py`` file.

   See :doc:`organizing_your_project` and the `Setuptool's
   documentation <https://pythonhosted.org/setuptools/>`_ for more
   information.

2. The package itself or a dependency of the package must include
   ``morepath`` in the ``install_requires`` list of the ``setup.py``
   file.

   Morepath only scans package that depend directly or indirectly on
   Morepath. It filters out packages which in no way depend on
   Morepath. So if your package has any Morepath configuration, you
   need to add ``morepath`` to ``install_requires``::

     setup(name='myapp'
       ...
       install_requires=[
         'morepath'
       ])

   If you set up your dependencies up correctly using
   ``install_requires`` this should be there anyway, or be a
   dependency of another dependency that's in
   ``install_requires``. Morepath just uses this information to do its
   scan.

3. The Python project name in ``setup.py`` should have the same name as
   the Python package name, *or* you use entry points to declare what should
   be scanned.

   Scan using naming convention:

     The project name defined by ``setup.py`` can be imported in
     Python as well: they have the same name. For example: if the
     project name is ``myapp``, the package that contains your code
     must be named ``myapp`` as well. (not ``my-app`` or ``MyApp`` or
     ``Elephant``):

     So if you have a ``setup.py`` like this::

       setup(
         name='myapp',
         packages=find_packages(),
         ...

     you should have a project directory structure like this::

        setup.py
        myapp
          __init__.py
          another_module.py

     In other words, the project name ``myapp`` can be imported::

       import myapp

     If you use a namespace package, you include the full name in the
     ``setup.py``::

      setup(
        name='my.app'
        packages=find_packages()
        namespace_packages=['my']
        ...

     This works with a project structure like this::

       setup.py
       my
         __init__.py
         app
           __init__.py
           another_module.py

     We recommend you use this naming convention as your Python
     projects get a consistent layout. But you don't have to -- you
     can use entry points too.

   Scan entry points:

     If for some reason you want a project name that is different from
     the package name you can still get it scanned automatically by
     Morepath. In this case you need to explicitly tell Morepath what
     to scan with an entry point in ``setup.py``::

       setup(name='elephant'
          ...
          entry_points={
              'morepath': [
                  'scan = my.package'
              ]
          }

     Note that you still need to have ``morepath`` in the
     ``install_requires`` list for this to work.

More information
----------------

Even more information and nitty gritty details can be found in the API
docs.  See :doc:`api`.
