Settings
========

Introduction
------------

A typical application has some settings: if an application logs, a
setting is the path to the log file. If an aplication sends email,
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

You can define a setting using the :meth:`AppBase.setting` directive::

  @app.setting(section="logging", name="logfile")
  def get_logfile():
      return "/path/to/logfile.log"

You can also use this directive to override a setting in another app::

  sub = morepath.App(extends=[app])
  @sub.setting(section="logging", name="logfile")
  def get_logfile_too():
     return "/a/different/logfile.log"

Settings are grouped logically: a setting is in a *section* and has a
*name*. This way you can organize all settings that deal with logging
under the ``logging`` section.

Accessing a setting
-------------------

During runtime, you can access the settings of the current application
using the :func:`morepath.settings` function, like this::

  settings().logging.logfile

In a tween factory (see :doc:tweens) or a directive implementation,
you can access a setting through the ``app`` object like this::

  app.settings.logging.logfile

Defining multiple settings
--------------------------

It can be convenient to define multiple settings in a section at once.
You can do this using the :meth:`AppBase.setting_section` directive::

  @app.setting_section(section="logging")
  def get_setting_section():
      return {
         'logfile': "/path/to/logfile.log",
         'loglevel': logging.WARNING
      }

You can mix ``setting`` and ``setting_section`` freely, but you cannot
define a setting multiple times in the same app, as this will result
in a configuration conflict.
