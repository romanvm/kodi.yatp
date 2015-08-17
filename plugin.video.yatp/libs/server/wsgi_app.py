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
import time
import re
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


def serve_file(file_, byte_position, torrent_handle, start_piece, piece_length):
    """
    Serve file by chunks

    Chunk == torrent piece.
    """
    while True:
        current_piece = start_piece + byte_position / piece_length
        # Wait for the piece if it is not downloaded
        while not torrent_handle.have_piece(current_piece):
            addon.log('...Waiting for piece #{0}...'.format(current_piece))
            if torrent_handle.piece_priority(current_piece) < 7:
                torrent_handle.piece_priority(current_piece, 7)
            time.sleep(0.1)
        torrent_handle.flush_cache()
        addon.log('Serving piece #{0}'.format(current_piece))
        file_.seek(byte_position)
        chunk = file_.read(piece_length)
        if not chunk:
            file_.close()
            break
        yield chunk
        byte_position += piece_length


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
    # if DEBUG:
    #     addon.log(reply)
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


@route('/stream/<path:path>')
def test_range_serving(path):
    """Test serving byte range"""
    addon.log('********* Test ***********')
    addon.log('Method: ' + request.method)
    addon.log('Headers: ' + str(request.headers.items()))
    file_path = os.path.normpath(os.path.join(download_dir, path))
    addon.log('File path: {0}'.format(file_path))
    size = os.path.getsize(file_path)
    addon.log('File size: {0}'.format(size))
    mime = MIME.get(os.path.splitext(path)[1], 'application/octet-stream')
    response.set_header('Content-Type', mime)
    response.set_header('Content-Length', str(size))
    response.set_header('Accept-Ranges', 'bytes')
    if request.method == 'GET':
        addon.log('Opening file...')
        body = open(file_path, 'rb')
        range_header = request.get_header('Range')
        streamed_file = torrent_client.streamed_file_data
        if range_header and streamed_file is not None:
            addon.log('Getting requested range')
            range_match = re.search(r'^bytes=(\d*)-(\d*)$', range_header)
            start_pos = int(range_match.group(1) or 0)
            end_pos = int(range_match.group(2) or size - 1)
            if end_pos - start_pos != 65536:
                if start_pos >= size or end_pos >= size:
                    addon.log('Error 416, Requested Range Not Satisfiable')
                    return HTTPError(416, 'Requested Range Not Satisfiable')
                response.status = 206
                response.set_header('Content-Length', str(end_pos - start_pos + 1))
                response.set_header('Content-Range', 'bytes {0}-{1}/{2}'.format(start_pos, end_pos, size))
                if start_pos > 0:
                    torrent_client.abort_buffering()
                    start_piece = streamed_file[1] + start_pos / streamed_file[4]
                    torrent_client.start_sliding_window_async(streamed_file[0],
                                                              start_piece,
                                                              start_piece + streamed_file[2],
                                                              streamed_file[3])
                    time.sleep(5.0)
                addon.log('Starting file chunks serving...')
                body = serve_file(body, start_pos, streamed_file[0], streamed_file[1], streamed_file[4])
            else:
                response.status = 200
        else:
            response.status = 200
    else:
        body = ''
    addon.log('Response status: {0}'.format(response.status))
    return body


app = default_app()
