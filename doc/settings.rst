Settings
========

Introduction
------------

A typical application has some settings: if an application logs, a
setting is the path to the log file. If an application sends email,
there are settings to control how email is sent, such as the email
address of the sender.

Applications that serve as frameworks for other applications may have
settings as well: the ``transaction_app`` defined by
`more.transaction`_ for instance has settings controlling
transactional behavior.

.. _`more.transaction`: https://github.com/morepath/more.transaction

Morepath has a powerful settings system that lets you define what
settings are available in your application and framework. It allows an
app that extends another app to override settings. This lets an app
that defines a framework can also define default settings that can be
overridden by the extending application if needed.

Defining a setting
------------------

You can define a setting using the :meth:`App.setting` directive::

  @App.setting(section="logging", name="logfile")
  def get_logfile():
      return "/path/to/logfile.log"

You can also use this directive to override a setting in another app::

  class Sub(App):
      pass

  @Sub.setting(section="logging", name="logfile")
  def get_logfile_too():
     return "/a/different/logfile.log"

Settings are grouped logically: a setting is in a *section* and has a
*name*. This way you can organize all settings that deal with logging
under the ``logging`` section.

Accessing a setting
-------------------

During runtime, you can access the settings of the current application
using the :attr:`morepath.App.settings` property::

  app.settings.logging.logfile

Remember that the current application is also accessible from the
request object::

  request.app.settings.logging.logfile


Defining multiple settings
--------------------------

It can be convenient to define multiple settings in a section at once.
You can do this using the :meth:`App.setting_section` directive::

  @App.setting_section(section="logging")
  def get_setting_section():
      return {
         'logfile': "/path/to/logfile.log",
         'loglevel': logging.WARNING
      }

You can mix ``setting`` and ``setting_section`` freely, but you cannot
define a setting multiple times in the same app, as this will result
in a configuration conflict.

Loading settings from a config file
-----------------------------------

.. testsetup:: *

  import os
  import morepath

  owd = os.getcwd()
  os.chdir(os.path.join(os.path.dirname(os.path.abspath(morepath.__file__)),
                        '../doc/code_examples'))

  class App(morepath.App):
      pass

.. testcleanup:: *

    os.chdir(owd)

For loading settings from a config file just load the file into a python
dictionary and pre-fill the settings with :meth:`morepath.App.init_settings`
before committing the app.

A example config file with YAML syntax could look like:

.. literalinclude:: code_examples/settings.yml

You can load it with:

.. testcode:: yaml

  import yaml

  with open('settings.yml') as config:
       settings_dict = yaml.load(config)

Remember to install ``pyyaml`` before importing ``yaml``.
For example with:

.. code-block:: console

  $ pip install pyyaml

The same config file with JSON syntax would look like:

.. literalinclude:: code_examples/settings.json

To load it use:

.. testcode:: json

  import json

  with open('settings.json') as config:
       settings_dict = json.load(config)

Now register the settings dictionary in the App settings
before starting the App:

.. testcode:: *

  App.init_settings(settings_dict)
  morepath.commit(App)

  app = App()

You can access the settings as before:

.. doctest:: *

   >>> app.settings.jinja2.extensions
   ['jinja2.ext.autoescape', 'jinja2.ext.i18n']

   >>> app.settings.jwtauth.algorithm
   'ES256'

   >>> app.settings.sqlalchemy.url
   'sqlite:///morepath.db'

You can also override and extend the settings by loading a config file in an
extending app as usual.
