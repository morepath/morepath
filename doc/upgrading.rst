Upgrading to a new Morepath version
===================================

Morepath keeps a detailed changelog (:doc:`changes`) that describes
what has changed in each release of Morepath. You can learn about new
features in Morepath this way, but also about things in your code that
might possibly break. Pay particular attention to entries marked
**Breaking change**, **Deprecated** and **Removed**.

**Breaking change** means that you have to update your code as
described if you use this feature of Morepath.

**Deprecated** means that your code won't break yet but you get a
deprecation warning instead. You can then upgrade your code to use the
newer APIs. You can show deprecation warnings by passing the following
flag to the Python interpreter when you run your code::

  $ python -W error::DeprecationWarning

If you use an entry point to create a command-line tool you will
have to supply your Python interpreter manually::

  $ python -W error::DeprecationWarning the_tool

You can also turn these on in your code::

  import warnings
  warnings.simplefilter('always', DeprecationWarning)

It's also possible to turn deprecation warnings into an error::

  import warnings
  warnings.simplefilter('error', DeprecationWarning)

A **Deprecated** entry in the changelog changes into a **Removed** in
a future release; we are not maintaining deprecation warnings
forever. If you see a **Removed** entry, it pays off to run your code
with deprecation warnings turned on before you upgrade to this
version.

