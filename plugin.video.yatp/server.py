# coding: utf-8
# Module: main
# Created on: 01.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Torrenter WSGI application and server
"""

import os
from inspect import getmembers, isfunction
from json import dumps
from time import sleep
import xbmc
import xbmcgui
from libs.addon import Addon
from libs import methods
from libs.bottle import Bottle, request, template, response, debug, static_file, TEMPLATE_PATH
from libs.wsgi_server import create_server
from libs.torrenter import Torrenter
from libs.timers import Timer, check_seeding_limits, save_resume_data

DEBUG = True

__addon__ = Addon()
static_path = os.path.join(__addon__.path, 'resources', 'web')
TEMPLATE_PATH.insert(0, os.path.join(static_path, 'templates'))
debug(DEBUG)
app = Bottle()
# These are the main torrent server parameters.
# Here they are hardcoded but in other implementations they can be read e.g. from a config file.
torrent_dir = __addon__.download_dir
resume_dir = os.path.join(__addon__.config_dir, 'torrents')
if not os.path.exists(resume_dir):
    os.mkdir(resume_dir)
max_ratio = __addon__.ratio_limit
max_time = __addon__.time_limit
TORRENT_PORT = 25335
SERVER_PORT = 8668
#-------------------------------------
torrenter = Torrenter(TORRENT_PORT, TORRENT_PORT + 10, True, resume_dir)
limits_timer = Timer(10, check_seeding_limits, torrenter, max_ratio, max_time)
save_resume_timer = Timer(20, save_resume_data, torrenter)


@app.route('/')
def root():
    """
    Root path

    :return:
    """
    return template('torrents')


@app.route('/json-rpc', method='GET')
def get_methods():
    """
    Display the list of available methods

    :return:
    """
    methods_list = []
    docs_list = []
    for member in getmembers(methods):
        if isfunction(member[1]) and not member[0].startswith('_'):
            methods_list.append(member[0])
            docs_list.append(member[1].__doc__.replace('\n', '<br>'))
    return template('methods', methods=methods_list, docs=docs_list)


@app.route('/json-rpc', method='POST')
def json():
    """
    JSON-RPC requests processing

    :return:
    """
    if DEBUG:
        __addon__.log('***** JSON request *****')
        __addon__.log(request.body.read())
    data = request.json
    # Use the default download dir if param[2] == ''
    if data['method'] == 'add_torrent' and len(data['params']) >= 2 and not data['params'][1]:
        data['params'][1] = torrent_dir
    # Use the default download dir if param[2] is missing
    elif data['method'] == 'add_torrent' and len(data['params']) == 1:
        data['params'].append(torrent_dir)
    if data['method'] == 'add_torrent' and len(data['params']) == 2:
        data['params'].append(True)
    reply = {'jsonrpc': '2.0', 'id': data.get('id', '1')}
    try:
        reply['result'] = getattr(methods, data['method'])(torrenter, data.get('params'))
    except Exception, ex:
        reply['error'] = '{0}: {1}'.format(str(ex.__class__)[7:-2], ex.message)
    if DEBUG:
        __addon__.log('***** JSON response *****')
        __addon__.log(str(reply))
    return reply


@app.route('/torrents-json')
def get_torrents():
    """
    Get the list of available torrents with their params wrapped in JSON

    :return:
    """
    response.content_type = 'application/json'
    return dumps(torrenter.get_all_torrents_info())


@app.route('/media/<path:path>')
def get_media(path):
    """
    Serve media files

    :param path: relative path to a media file
    :return:
    """
    print path
    if os.path.splitext(path)[1] == '.mkv':
        mime = 'video/x-matroska'
    elif os.path.splitext(path)[1] == '.mp4':
        mime = 'video/mp4'
    elif os.path.splitext(path)[1] == '.avi':
        mime = 'video/avi'
    elif os.path.splitext(path)[1] == '.ts':
        mime = 'video/mp2t'
    elif os.path.splitext(path)[1] == '.mov':
        mime = 'video/quicktime'
    else:
        mime = 'auto'
    return static_file(path, root=torrent_dir, mimetype=mime)


@app.route('/static/<path:path>')
def get_static(path):
    """
    Serve static files

    :param path: relative path to a static file
    :return:
    """
    return static_file(path, root=static_path)


if __name__ == '__main__':
    __addon__.log('***** Torrent Server starting... *******')
    sleep(3.0)
    start_trigger = True
    httpd = create_server(app, port=SERVER_PORT)
    httpd.timeout = 0.1
    limits_timer.start()
    save_resume_timer.start()
    while not xbmc.abortRequested:
        httpd.handle_request()
        if start_trigger:
            xbmcgui.Dialog().notification('YATP', 'Torrent server started', __addon__.icon, 3000, False)
            __addon__.log('***** Torrent Server started *******')
            start_trigger = False
    limits_timer.abort()
    torrenter.abort_buffering()
    del torrenter
    __addon__.log('***** Torrent Server stopped *******')
