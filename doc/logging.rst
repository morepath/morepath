Logging
=======

Directive logging
-----------------

Morepath has support for logging directive execution. This can be
helpful when debugging why your Morepath application does not do what
was expected. Morepath's directive logging makes use of Python's
logging_ module, which is very flexible.

.. _logging: https://docs.python.org/2/library/logging.html

To get the complete log of directive executions, you can set up the
following code in your project::

  directive_logger = logging.getLogger('morepath.directive')
  directive_logger.addHandler(logging.StreamHandler())
  directive_logger.setLevel(logging.DEBUG)

The ``StreamHandler`` logs messages to ``stderr``. You can reconfigure
this or use another handler altogether. You need to change the log
level so that ``logging.DEBUG`` level messages are also shown, as
Morepath's directive logging uses this log level.

You can also configure it to just see the output for one particular directive.
To see all ``path`` directive executed in your project you'd
change the ``getLogger`` statement to this::

  directive_logger = logging.getLogger('morepath.directive.path')

The Python logging module has many more options, but this should get
you started.
