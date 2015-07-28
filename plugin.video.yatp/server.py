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

import sys
from libs.server.addon import Addon

standalone = '-s' in sys.argv or '--standalone' in sys.argv
addon = Addon()

if not standalone:
    if addon.remote_mode:
        sys.exit()
    from time import sleep
    import xbmc
    import xbmcgui
    sleep(3.0)
addon.log('***** Starting Torrent Server... *****')

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
