from wsgiref.simple_server import make_server


def run(wsgi, host=None, port=None):  # pragma: no cover
    """Uses wsgiref.simple_server to run application for debugging purposes.

    Don't use this in production; use an external WSGI server instead,
    for instance Apache mod_wsgi, Nginx wsgi, Waitress, Gunicorn.

    :param wsgi: WSGI app.
    :param host: hostname.
    :param port: port.
    """
    if host is None:
        host = '127.0.0.1'
    if port is None:
        port = 5000
    server = make_server(host, port, wsgi)
    print("Running %s with wsgiref.simple_server on http://%s:%s" % (
        wsgi, host, port))
    server.serve_forever()
