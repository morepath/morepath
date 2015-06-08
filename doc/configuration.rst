Configuration
=============

Introduction
------------

When you define a :doc:`view <views>`, a :doc:`path <paths_and_linking>`,
a :doc:`setting <settings>`, a :doc:`tween <tweens>`, or if a third party
package defines that for you, Morepath needs to be told about it.

This is called the Morepath *configuration*.


How it works
------------

Morepath needs to be configured before it is run. That means that you need
to run the necessary configuration steps, before you pass a new instance
of your application to your WSGI server::

  if __name__ == '__main__':
      config = morepath.setup()
      config.scan()
      config.commit()

      application = App()
      morepath.run(application)

Morepath always scans itself first, then whatever packages you wish to
scan. In the example above, it scans itself during ``morepath.setup``, handing
over the configuration object to you.

``config.scan`` then scans whatever package it is handed. If it receives
no package, it scans the package it is called from. That's the current
file in the example above.

Once all scanning is completed, the configuration is committed and the
application may be run.

Scanning dependencies
---------------------

Morepath is a micro-framework at its core. It's very extensible however, so you
can expand it with other packages that add extra functionality to it. For
instance, you can use
`more.chameleon <https://github.com/morepath/more.chameleon>`_
for templating or
`more.transaction <https://github.com/morepath/more.transaction>`_
for SQLAlchemy integration.

These packages bring their own Morepath configuration to the table. Said
configuration also needs to be loaded by Morepath before Morepath is run.

Manual scan
~~~~~~~~~~~

The most explicit way of scanning your dependencies is a manual scan.

Say you depend on `more.jinja2 <https://github.com/morepath/more.jinja2>`_
and you want to extend the the first example.

This is what you do::

  import more.jinja2

  if __name__ == '__main__':
      config = morepath.setup()
      config.scan(more.jinja2)
      config.scan()
      config.commit()

      application = App()
      morepath.run(application)

As you can see, you need to import your dependency and scan it using
``config.scan``. If you have more dependencies, just add them in this fashion.

Automatic scan
~~~~~~~~~~~~~~

Manual scanning can get tedious as you need to add each and every new
dependency that you rely on.

Instead, you may use the ``autoconfig`` method, which tries to scan
all packages depending on Morepath. To use this method, the example from above
has to be changed slightly.

Note how we no longer use ``morepath.setup``::

  if __name__ == '__main__':
      config = morepath.autoconfig()
      config.scan()
      config.commit()

      application = App()
      morepath.run(application)

As you can see, we also don't need to import any dependencies anymore. We still
need to run ``config.scan`` without parameters however, so our own file gets
scanned.

That is, unless we move all our configuration into a separate package as well.
Then the file containing the configuration code might not need scanning.

Autosetup
~~~~~~~~~

In the previous example we still needed to scan the startup module itself,
so that is why we need ``config.scan()``. Instead, you can however turn your
code into a full Morepath project with a setup.py and do away with this
requirement.

See :doc:`organizing_your_project`.

Once all your configuration is done inside of projects, you can simplify your
scan further::

  if __name__ == '__main__':
      morepath.autosetup()
      morepath.run(App())

Writing scannable packages
~~~~~~~~~~~~~~~~~~~~~~~~~~

When Morepath looks for packages that it can scan, it has a few requirements
that each package has to fulfill to be considered.

1. The package must be made available using a ``setup.py`` file.

  See `Setuptool's documentation <https://pythonhosted.org/setuptools/>`_
  for more information.

2. The package itself or a dependency of the package must include ``morepath``
   in the ``install_requires`` list of the ``setup.py`` file.

  To avoid having to scan *all* packages, Morepath filters out packages which
  in no way depend on Morepath. If your package does, you need to add
  ``morepath`` to ``install_requires``::

    setup(name='mypackage'
      ...
      install_requires=[
        'morepath'
      ])

3. The Python package must be either importable by naming convention or by
   using entry points.

  By naming convention:

    Meaning the project name defined in ``setup.py`` is importable in
    Python. For example: if the project inside the package is named ``myapp``,
    the package must be named ``myapp`` as well (not ``my-app`` or ``MyApp``):

    So if you have a ``setup.py`` like this::

      setup(name='myapp'
        ...

    And a directory structure like this::

      myapp/__init__p.py
      setup.py

    Then this works::

      import myapp

    But this does not::

      import my-app
      import MyApp

    If you use a namespace package, you include the full name in the
    ``setup.py``::

      setup(name='my.app'
        ...

    And use a structure like this::

       my/app/__init__.py
       setup.py

    If you do not follow this naming convention, you don't need to rename
    everything though, you may also tell Morepath explicitly what to do by
    using entry points.

  With entry points:

    You may have a reason for the project name to be different from the package
    name. In this case you need to tell Morepath what to scan::

      setup(name='my-package'
        ...
        entry_points={
            'morepath': [
                'scan = my.package'
            ]
        }

    Note that you still need to have ``morepath`` in the ``install_requires``
    list for this to work.

More information
----------------

Even more information and nitty gritty details can be found in the API docs.
See :doc:`api`.
