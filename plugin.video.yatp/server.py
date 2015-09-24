# coding: utf-8
# Module: server
# Created on: 01.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Torrent streamer WSGI server
"""

import sys
import xbmc
from libs.server.addon import Addon


addon = Addon()
if not addon.start_server:
    addon.log('Torrent Server is disabled in Settings.', xbmc.LOGWARNING)
    sys.exit()

from time import sleep
import xbmcgui
from libs.server import wsgi_app
from libs.server.wsgi_server import create_server


sleep(2.0)
addon.log('***** Starting Torrent Server... *****')
if addon.enable_limits:
    wsgi_app.limits_timer.start()
if addon.persistent:
    wsgi_app.save_resume_timer.start()
wsgi_app.log_torrents_timer.start()
httpd = create_server(wsgi_app.app, port=addon.server_port)
httpd.timeout = 0.2
start_trigger = True
while not xbmc.abortRequested:
    httpd.handle_request()
    if start_trigger:
        addon.log('***** Torrent Server started *****', xbmc.LOGNOTICE)
        xbmcgui.Dialog().notification('YATP', addon.get_localized_string(32028), addon.icon, 3000, False)
        start_trigger = False
addon.log('***** Torrent Server stopped *****', xbmc.LOGNOTICE)
wsgi_app.torrent_client.abort_buffering()
if addon.enable_limits:
    wsgi_app.limits_timer.abort()
if addon.persistent:
    wsgi_app.save_resume_timer.abort()
wsgi_app.log_torrents_timer.abort()
del wsgi_app.torrent_client
