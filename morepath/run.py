from __future__ import annotations

import sys
from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from argparse import ArgumentParser
    from collections.abc import Callable
    from wsgiref.simple_server import WSGIServer

    from .types import WSGIApplication


def make_parser(
    prog: str | None, default_host: str, default_port: int
) -> ArgumentParser:
    """Make a command-line parser with host and port arguments.

    :param prog: the name of the program
    :param default_host: the default value for the host argument
    :param default_port: the default value for the port argument
    :return: an instance of ArgumentParser
    """
    import argparse

    def unsigned_short(s: str) -> int:
        v = int(s)
        if not 0 <= v <= 65536:
            raise ValueError
        return v

    unsigned_short.__name__ = "integer in 0..65535"

    parser = argparse.ArgumentParser(
        prog=prog, formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "-p", "--port", type=unsigned_short, help="TCP port on which to listen"
    )
    parser.add_argument(
        "-H", "--host", help="hostname or IP address on which to listen"
    )
    parser.set_defaults(host=default_host, port=default_port)
    return parser


def run(
    wsgi: WSGIApplication,
    host: str = "127.0.0.1",
    port: int = 5000,
    prog: str | None = None,
    ignore_cli: bool = False,
    callback: Callable[[WSGIServer], object] | None = None,
) -> NoReturn:
    """Uses wsgiref.simple_server to run an application for debugging purposes.

    By default, this function looks at the command line for arguments
    specified with the ``--host`` or ``--port`` options. These
    override the actual arguments passed to this function.  Use
    ``ignore_cli=True`` to disable this behavior.

    Under non-exceptional circumstances this function never returns.

    Don't use this in production; use an external WSGI server instead,
    for instance Apache mod_wsgi, Nginx wsgi, Waitress, Gunicorn.

    :param callable wsgi: WSGI app.
    :param str host: hostname or IP address on which to listen.
    :param int port: TCP port on which to listen.
    :param prog: the name of the program displayed by diagnostics and help.
    :type prog: str or None
    :param bool ignore_cli: whether to ignore ``sys.argv``.
    :param callback: function invoked after the creation of the server.
    :type callback: function(server) or None
    :return: never.

    .. note::

      Unless ``ignore_cli`` is true, this function provides a
      full-featured command-line parser. Its help message describes
      how to use it:

      .. code-block::

        usage: <script name> [-h] [-p PORT] [-H HOST]

        options:
          -h, --help       show this help message and exit
          -p, --port PORT  TCP port on which to listen (default: 5000)
          -H, --host HOST  hostname or IP address on which to listen
                           (default: 127.0.0.1)

      The default values for the ``--port`` and ``--host`` options are
      taken from the value of the arguments passed to :func:`morepath.run`.

    """
    import errno
    from wsgiref.simple_server import make_server

    parser = make_parser(prog, host, port)
    args = parser.parse_args([] if ignore_cli else None)

    try:
        server = make_server(args.host, args.port, wsgi)
    except OSError as ex:
        hint = ""
        if ex.errno == errno.EADDRINUSE and not ignore_cli:
            hint = "\n  Use '--port PORT' to specify a different port.\n\n"
        parser.exit(
            1 if ex.errno is None else ex.errno,
            f"{parser.prog}: {ex}: {args.host}:{args.port}\n" + hint,
        )

    if callback is not None:
        callback(server)

    print(f"Running {wsgi}")
    print(
        # FIXME: Do we want to try to coerce from bytes to str, if we get
        #        bytes or a bytearray?
        "Listening on http://{}:{}".format(  # type: ignore[str-bytes-safe]
            server.server_address[0], server.server_port
        )
    )
    print("Press Ctrl-C to stop...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt.")

    sys.exit(0)
