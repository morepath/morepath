import dectate
import importscan
from .app import App


class Config(object):
    """Providing backwards compatiblity with APIs before Morepath 0.13.

    Use the new :func:`commit` or :func:`autocommit` functions instead.
    """
    def scan(self, package, ignore=None, handle_error=None):
        """Scan configuration.

        Note that this is not entirely backwards compatible if you
        passed third error handling argument before. Instead see
        :func:`importscan.scan` for the new behavior.

        Scan also behaves differently in that it cannot be executed
        again for the same package -- the registration of any
        :class:`App` classes has already happened and cannot be
        repeated.
        """
        importscan.scan(package, ignore, handle_error)

    def commit(self):
        """Commit configuration.
        """
        dectate.commit([App])
        dectate.autocommit()
        dectate.clear_autocommit()


def setup():
    """Set up core Morepath framework configuration.

    Provided for BACKWARDS COMPATIBILITY only.

    Returns a :class:`Config` object; you can then :meth:`Config.scan`
    the configuration of other packages you want to load and then
    :meth:`Config.commit` it.

    See also :func:`autoconfig` and :func:`autosetup`.

    :returns: :class:`Config` object.
    """
    return Config()
