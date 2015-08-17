# coding: utf-8
# Module: wsgi_app
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
from torrenter import Streamer, libtorrent
from timers import Timer, check_seeding_limits, save_resume_data


MIME = {'.mkv': 'video/x-matroska',
        '.mp4': 'video/mp4',
        '.avi': 'video/avi',
        '.ts': 'video/mp2t',
        '.m2ts': 'video/mp2t',
        '.mov': 'video/quicktime'}

addon = Addon()
# Torrent client parameters
download_dir = addon.download_dir
resume_dir = os.path.join(addon.config_dir, 'torrents')
if not os.path.exists(resume_dir):
    os.mkdir(resume_dir)
torrent_port = addon.torrent_port
torrent_client = Streamer(torrent_port, torrent_port + 10,
                          addon.dl_speed_limit, addon.ul_speed_limit, True, resume_dir)
# Timers
max_ratio = addon.ratio_limit
max_time = addon.time_limit
limits_timer = Timer(10, check_seeding_limits, torrent_client, max_ratio, max_time,
                     addon.expired_action, addon.delete_expired_files)
save_resume_timer = Timer(30, save_resume_data, torrent_client)
# Bottle WSGI application
static_path = os.path.join(addon.path, 'resources', 'web')
TEMPLATE_PATH.insert(0, os.path.join(static_path, 'templates'))
debug(DEBUG)


@route('/')
def root():
    """
    Root path

    :return:
    """
    login, password = request.auth or (None, None)
    if addon.pass_protect and (login is None or (login, password) != addon.credentials):
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
    info = methods.__doc__.replace('\n', '<br>')
    return template('methods', methods=methods_list, docs=docs_list, info=info)


@route('/json-rpc', method='POST')
def json_rpc():
    """
    JSON-RPC requests processing

    :return:
    """
    if DEBUG:
        addon.log('***** JSON request *****')
        addon.log(request.body.read())
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
        reply['result'] = getattr(methods, data['method'])(torrent_client, data.get('params'))
    except Exception, ex:
        reply['error'] = '{0}: {1}'.format(str(ex.__class__)[7:-2], ex.message)
    if DEBUG:
        addon.log('***** JSON response *****')
        addon.log(str(reply))
    return reply


@route('/torrents-json')
def get_torrents():
    """
    Get the list of available torrents with their params wrapped in JSON

    :return:
    """
    response.content_type = 'application/json'
    reply = dumps(torrent_client.get_all_torrents_info())
    if DEBUG:
        addon.log(reply)
    return reply


@route('/media/<path:path>')
def get_media(path):
    """
    Serve media files

    :param path: relative path to a media file
    :return:
    """
    if DEBUG:
        addon.log('Media file requested')
        addon.log('Method: ' + request.method)
        addon.log('Headers: ' + str(request.headers.items()))
    addon.log('Playing media: ' + path)
    if sys.platform == 'win32':
        path = path.decode('utf-8')
    return static_file(path, root=download_dir, mimetype=MIME.get(os.path.splitext(path)[1], 'auto'))


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
    if request.forms.get('sub_path'):
        path = os.path.join(download_dir, request.forms.get('sub_path'))
    else:
        path = download_dir
    torrent_client.add_torrent_async(torrent, path)


app = default_app()
