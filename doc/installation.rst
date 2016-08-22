Installation
============

Quick and Dirty Installation
----------------------------

To get started with Morepath right away, first create a Python 3.5
virtualenv_::

  $ virtualenv morepath_env
  $ source morepath_env/bin/activate

Now install Morepath into it::

  $ pip install morepath

You can now use the virtual env's Python to run any code that uses
Morepath::

  $ python quickstart.py

See :doc:`quickstart` for information on how to get started with
Morepath itself, including an example of ``quickstart.py``.

.. _virtualenv: http://www.virtualenv.org/

.. _cookiecutter:

Creating a Morepath Project Using Cookiecutter
----------------------------------------------

Morepath provides an official cookiecutter template. Cookiecutter is a tool
that creates projects through project templates. Morepath's template comes
with a very simple application, either in RESTful or traditional HTML flavor.

Follow the instructions on Morepath's cookiecutter template repository to
get started:

`<https://github.com/morepath/morepath-cookiecutter>`_

This is a great way to get started with Morepath as a beginner or to start
a new project as a seasoned Morepath user.

Creating a Morepath Project Manually
------------------------------------

When you develop a web application it's a good idea to use standard
Python project organization practices. :doc:`organizing_your_project`
has some recommendations on how to do this with Morepath. Relevant in
particular is the contents of ``setup.py``, which depends on Morepath
and also sets up an entry point to start the web server.

Once you have a project you can use tools like pip_.
We'll briefly describe how to it.

.. _pip: http://www.pip-installer.org/

pip
~~~


With pip and a virtualenv called ``morepath_env``, you can do this in
your project's root directory::

  $ pip install --editable .

You can now run the application like this (if you called the console
script ``myproject-start``)::

  $ myproject-start

Depending on Morepath development versions
------------------------------------------

If you like being on the cutting edge and want to depend on the latest
Morepath and Reg development versions always, you can install these using
pip (in a virtualenv). Here's how::

  $ pip install git+git://github.com/morepath/reg.git@master

  $ pip install git+git://github.com/morepath/morepath.git@master

A more involved method how to install Morepath for development is described
in :doc:`developing`.
