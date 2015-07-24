# coding: utf-8
# Module: server
# Created on: 01.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Torrent streamer WSGI server
"""

from time import sleep

sleep(3.0)

from libs.addon import Addon

__addon__ = Addon()
__addon__.log('***** Starting Torrent Server... *****')

import xbmc
import xbmcgui
from libs.server import wsgi
from libs.server.wsgi_server import create_server

wsgi.limits_timer.start()
wsgi.save_resume_timer.start()
httpd = create_server(wsgi.application, port=__addon__.server_port)
httpd.timeout = 0.1
start_trigger = True
while not xbmc.abortRequested:
    httpd.handle_request()
    if start_trigger:
        xbmcgui.Dialog().notification('YATP', 'Torrent server started', __addon__.icon, 3000, False)
        __addon__.log('***** Torrent Server started *****')
        start_trigger = False
wsgi.limits_timer.abort()
wsgi.save_resume_timer.abort()
wsgi.torrenter.abort_buffering()
del wsgi.torrenter
__addon__.log('***** Torrent Server stopped *****')
