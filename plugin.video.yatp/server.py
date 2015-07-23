# coding: utf-8
# Module: server
# Created on: 01.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Torrent streamer WSGI server
"""

from libs.addon import Addon
__addon__ = Addon()
__addon__.log('***** Starting Torrent Server... *****')

from time import sleep
import xbmc
import xbmcgui
from libs import wsgi
from libs.wsgi_server import create_server

server_port = __addon__.server_port
sleep(3.0)
start_trigger = True
httpd = create_server(wsgi.application, port=server_port)
httpd.timeout = 0.1
wsgi.limits_timer.start()
wsgi.save_resume_timer.start()
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
