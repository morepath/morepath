# flake8: noqa
from .app import App
from .implicit import initialize
from .setup import setup
from morepath import directive # register directive methods
from .view import render_json, render_html
from .request import Request, Response
from .config import Config
from werkzeug.utils import redirect
from morepath.autosetup import autoconfig, autosetup

#initialize()
