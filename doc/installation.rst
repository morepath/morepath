Installation
============

**Note**: Morepath is not yet released. This document includes some
quick notes on how to set up Morepath for your own project, using
virtualenv and pip. The :doc:`developing` section contains information
on how to set up Morepath for its own development.

First set up a Python 2.7 virtualenv for your project::

  $ virtualenv /path/to/mp

Then install the development version of Morepath with ``pip``::

  $ /path/to/mp/bin/pip install git+git://github.com/morepath/morepath.git@master

This requires a release of the Reg library, which may not always be
present. You can always install a development version of Reg
manually::

  $ /path/to/mp/bin/pip install git+git://github.com/morepath/reg.git@master

