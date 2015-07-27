#!/usr/bin/env python2
# coding: utf-8
# Module: server
# Created on: 01.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Torrent streamer WSGI server

To start the server in standalone mode (without Kodi)
use -s or --standalone command line parameter, e.g.:
python server.py --standalone
"""
# todo: investigate unwanted auto-pausing newly added torrents

import sys
standalone = '-s' in sys.argv or '--standalone' in sys.argv

if not standalone:
    from time import sleep
    sleep(3.0)

from libs.addon import Addon

addon = Addon()
addon.log('***** Starting Torrent Server... *****')

try:
    import xbmc
    import xbmcgui
except ImportError:
    pass
from libs.server import wsgi_app
from libs.server.wsgi_server import create_server

wsgi_app.limits_timer.start()
wsgi_app.save_resume_timer.start()
httpd = create_server(wsgi_app.app, port=addon.server_port)
httpd.timeout = 0.1
start_trigger = True
try:
    while standalone or not xbmc.abortRequested:
            httpd.handle_request()
            if start_trigger:
                addon.log('***** Torrent Server started *****')
                if not standalone:
                    xbmcgui.Dialog().notification('YATP', 'Torrent server started', addon.icon, 3000, False)
                else:
                    print 'Press CTRL+C to exit'
                start_trigger = False
except KeyboardInterrupt:
    pass
wsgi_app.limits_timer.abort()
wsgi_app.save_resume_timer.abort()
wsgi_app.torrenter.abort_buffering()
del wsgi_app.torrenter
addon.log('***** Torrent Server stopped *****')
