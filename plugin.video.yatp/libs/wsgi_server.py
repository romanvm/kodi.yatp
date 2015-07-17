# coding: utf-8
# Module: wsgi_server
# Created on: 01.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

from wsgiref.simple_server import WSGIServer, WSGIRequestHandler
from SocketServer import ThreadingMixIn


class CustomWSGIRequestHandler(WSGIRequestHandler):
    """Custom WSGI Request Handler"""
    def log_message(self, format, *args):
        """Disable log messages"""
        pass


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    """Multi-threaded WSGI server"""
    daemon_threads = True


def create_server(app, host='', port=8000):
    """
    Create a new WSGI server listening on 'host' and 'port' for WSGI app
    """
    httpd = ThreadedWSGIServer((host, port), CustomWSGIRequestHandler)
    httpd.set_app(app)
    return httpd
