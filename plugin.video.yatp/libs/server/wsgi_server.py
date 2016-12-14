# coding: utf-8
# Module: wsgi_server
# Created on: 01.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Custom WSGI Server and RequestHandler
"""

from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
from SocketServer import ThreadingMixIn


class SilentWSGIRequestHandler(WSGIRequestHandler):
    """Custom WSGI Request Handler with logging disabled"""
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args, **kwargs):
        """Disable log messages"""
        pass


class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    """Multi-threaded WSGI server"""
    allow_reuse_address = True
    daemon_threads = True


def create_server(app, host='', port=8668):
    """
    Create a new WSGI server listening on 'host' and 'port' for WSGI app
    """
    return make_server(host, port, app,
                       server_class=ThreadedWSGIServer,
                       handler_class=SilentWSGIRequestHandler)
