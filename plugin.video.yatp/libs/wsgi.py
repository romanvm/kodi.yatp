# coding: utf-8
# Module: wsgi
# Created on: 23.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
"""
Torrent streamer WSGI application for Web/JSON interface
"""

DEBUG = True

import os
import sys
from cStringIO import StringIO
from json import dumps
from inspect import getmembers, isfunction
from bottle import route, default_app, request, template, response, debug, static_file, TEMPLATE_PATH, HTTPError
import methods
from addon import Addon
from torrenter import Torrenter, libtorrent
from timers import Timer, check_seeding_limits, save_resume_data

__addon__ = Addon()
# Torrent client parameters
download_dir = __addon__.download_dir
resume_dir = os.path.join(__addon__.config_dir, 'torrents')
if not os.path.exists(resume_dir):
    os.mkdir(resume_dir)
torrent_port = __addon__.torrent_port
torrenter = Torrenter(torrent_port, torrent_port + 10, True, resume_dir)
# Timers
max_ratio = __addon__.ratio_limit
max_time = __addon__.time_limit
limits_timer = Timer(10, check_seeding_limits, torrenter, max_ratio, max_time,
                     __addon__.expired_action, __addon__.delete_expired_files)
save_resume_timer = Timer(20, save_resume_data, torrenter)
# Bottle WSGI application
static_path = os.path.join(__addon__.path, 'resources', 'web')
TEMPLATE_PATH.insert(0, os.path.join(static_path, 'templates'))
debug(DEBUG)


@route('/')
def root():
    """
    Root path

    :return:
    """
    login, password = request.auth or (None, None)
    if __addon__.pass_protect and (login is None or (login, password) != __addon__.credentials):
        error = HTTPError(401, 'Access denied')
        error.add_header('WWW-Authenticate', 'Basic realm="private"')
        return error
    else:
        return template('torrents')


@route('/json-rpc', method='GET')
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


@route('/json-rpc', method='POST')
def json_rpc():
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
        data['params'][1] = download_dir
    # Use the default download dir if param[2] is missing
    elif data['method'] == 'add_torrent' and len(data['params']) == 1:
        data['params'].append(download_dir)
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


@route('/torrents-json')
def get_torrents():
    """
    Get the list of available torrents with their params wrapped in JSON

    :return:
    """
    response.content_type = 'application/json'
    return dumps(torrenter.get_all_torrents_info())


@route('/media/<path:path>')
def get_media(path):
    """
    Serve media files

    :param path: relative path to a media file
    :return:
    """
    __addon__.log('Playing media: ' + path.decode('utf-8'))
    if sys.platform == 'win32':
        path = path.decode('utf-8')
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
    return static_file(path, root=download_dir, mimetype=mime)


@route('/static/<path:path>')
def get_static(path):
    """
    Serve static files

    :param path: relative path to a static file
    :return:
    """
    return static_file(path, root=static_path)


@route('/add-torrent/<source>', method='POST')
def add_torrent(source):
    """
    Add .torrent file or torrent link

    :param source: 'file' or 'link'
    :return:
    """
    if source == 'file':
        buffer_ = StringIO()
        upload = request.files.get('torrent_file')
        upload.save(buffer_)
        torrent = libtorrent.bdecode(buffer_.getvalue())
    else:
        torrent = request.forms.get('torrent_link')
    path = os.path.join(download_dir, os.path.normpath(request.forms.get('sub_path')))
    torrenter.add_torrent_async(torrent, path)


application = default_app()
