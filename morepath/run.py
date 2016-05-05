import sys


def make_parser(prog, default_host, default_port):
    """Make a command-line parser with host and port arguments.

    :param prog: the name of the program
    :param default_host: the default value for the host argument
    :param default_port: the default value for the port argument
    :return: an instance of ArgumentParser
    """
    import argparse

    def unsigned_short(s):
        v = int(s)
        if not 0 <= v <= 65536:
            raise ValueError
        return v
    unsigned_short.__name__ = 'integer in 0..65535'

    parser = argparse.ArgumentParser(
        prog=prog,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-p", "--port", type=unsigned_short,
        help="TCP port on which to listen")
    parser.add_argument(
        "-H", "--host",
        help="hostname or IP address on which to listen")
    parser.set_defaults(host=default_host, port=default_port)
    return parser


def run(
        wsgi,
        host='127.0.0.1',
        port=5000,
        prog=None,
        ignore_cli=False,
        callback=None):
    """Uses wsgiref.simple_server to run an application for debugging purposes.

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
    """
    import socket
    from wsgiref.simple_server import make_server

    parser = make_parser(prog, host, port)
    args = parser.parse_args([] if ignore_cli else None)

    try:
        server = make_server(args.host, args.port, wsgi)
    except socket.error as ex:
        parser.exit(ex.errno, '{}: {}: {}:{}\n'.format
                    (parser.prog, ex, args.host, args.port))

    if callback is not None:
        callback(server)

    print("Running {}".format(wsgi))
    print("Listening on http://{}:{}".format(
        server.server_address[0], server.server_port))
    print("Press Ctrl-C to stop...")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nReceived keyboard interrupt.")

    sys.exit(0)
