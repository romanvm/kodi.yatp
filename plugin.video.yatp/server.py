# coding: utf-8
# Module: server
# Created on: 01.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Torrent streamer WSGI server
"""

from time import sleep
import xbmc
import xbmcgui
from libs.server.addon import Addon
from libs.server import wsgi_app
from libs.server.wsgi_server import create_server


addon = Addon()
sleep(2.0)
addon.log('***** Starting Torrent Server... *****')
wsgi_app.limits_timer.start()
wsgi_app.save_resume_timer.start()
httpd = create_server(wsgi_app.app, port=addon.server_port)
httpd.timeout = 0.1
start_trigger = True
while not xbmc.abortRequested:
        httpd.handle_request()
        if start_trigger:
            addon.log('***** Torrent Server started *****')
            xbmcgui.Dialog().notification('YATP', addon.get_localized_string(32028), addon.icon, 3000, False)
            start_trigger = False
wsgi_app.limits_timer.abort()
wsgi_app.save_resume_timer.abort()
wsgi_app.torrent_client.abort_buffering()
del wsgi_app.torrent_client
addon.log('***** Torrent Server stopped *****')
