import morepath
import errno
import re
from .fixtures import basic
import pytest


def test_run_port_out_of_range(mockserver, capsys):
    "Fail gracefully if the port is out of range."
    mockserver.set_argv(['--port', '-3'])

    assert mockserver.run(basic.app()) == 2

    out, err = capsys.readouterr()

    assert err == """\
usage: script-name [-h] [-p PORT] [-H HOST]
script-name: error: argument -p/--port: invalid integer in 0..65535 value: '-3'
"""
    assert out == ''


def test_run_socketerror(mockserver, capsys):
    """Fail gracefuly on a socket error.

    In this case the error is triggered by listening on example.com.

    """
    mockserver.set_argv(['--host', 'example.com'])

    assert mockserver.run(basic.app()) != 0

    out, err = capsys.readouterr()

    # The wording of the error message is system-specific.
    assert re.match('script-name: .*: example.com:5000', err)
    assert out == ''


def test_run_defaults(mockserver, capsys):
    "The arguments to makeserver form the defaults for the CLI."
    mockserver.set_argv(['script-name', '--help'])

    assert mockserver.run(basic.app(), host='localhost', port=80) == 0

    out, err = capsys.readouterr()

    assert err == ''
    assert out == """\
usage: script-name [-h] [-p PORT] [-H HOST]

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  TCP port on which to listen (default: 80)
  -H HOST, --host HOST  hostname or IP address on which to listen (default:
                        localhost)
"""


def test_run(mockserver, capsys):
    "Run with a mocked server."
    mockserver.set_argv(['--port', '0'])

    assert mockserver.run(basic.app()) == 0

    out, err = capsys.readouterr()

    assert err == ''
    assert re.match("""\
Running <morepath.tests.fixtures.basic.app object at 0x[0-9a-f]+>
Listening on http://127.0.0.1:\\d+
Press Ctrl-C to stop...

Received keyboard interrupt.""", out)


def test_run_hint_on_eaddrinuse(mockserver, capsys):
    """Fail not only gracefully but also helpfully on EADDRINUSE.

    In this case having a second server (mockserver) listening on the
    same port as a first server triggers the socket error.

    """

    def with_existing(first_server):
        used_port = first_server.server_port
        # setup a second server on exactly the same port
        mockserver.set_argv(['--port', str(used_port)])
        assert mockserver.run(basic.app()) == errno.EADDRINUSE

        out, err = capsys.readouterr()

        # The wording of the error message is system-specific.
        rex = """\
script-name: .*: 127.0.0.1:{}

  Use '--port PORT' to specify a different port.

""".format(used_port)

        assert re.match(rex, err)
        assert out == ''

        # If ignore_cli is True, we don't get the helpful hint
        assert mockserver.run(
            basic.app(),
            port=used_port,
            ignore_cli=True
        ) == errno.EADDRINUSE

        out, err = capsys.readouterr()

        rex = 'script-name: .*: 127.0.0.1:{}\n'.format(used_port)
        assert re.match(rex, err)
        assert out == ''

    # setup a first server
    with pytest.raises(SystemExit) as ex:
        morepath.run(
            basic.app(),
            port=0,
            prog='first-server',
            callback=with_existing,
            ignore_cli=True)
    assert ex.value.code == 0


def test_run_actual(capsys):
    from threading import Thread

    def query(url, completion_callback, response):
        try:
            from urllib import urlopen
        except ImportError:
            from urllib.request import urlopen
        try:
            response.append(urlopen(url).read())
        except Exception as ex:
            response.append(ex)
        finally:
            completion_callback()

    response = []

    def callback(server):
        thread = Thread(target=query, args=(
            'http://127.0.0.1:{}'.format(server.server_port),
            server.shutdown, response))
        thread.daemon = True
        thread.start()

    with pytest.raises(SystemExit) as ex:
        morepath.run(
            basic.app(),
            port=0,
            prog='script-name',
            callback=callback,
            ignore_cli=True)

    assert ex.value.code == 0

    assert response == [b'The root: ROOT']

    out, err = capsys.readouterr()

    assert re.match("""\
Running <morepath.tests.fixtures.basic.app object at 0x[0-9a-f]+>
Listening on http://127.0.0.1:\\d+
Press Ctrl-C to stop...
""", out)
    assert re.match(r'127.0.0.1 - - \[.*?\] "GET / HTTP/1.[01]" 200 14', err)
