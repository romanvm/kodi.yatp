# coding: utf-8
# Module: wsgi_app
# Created on: 23.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Torrent streamer WSGI application for Web/JSON interface
"""

import os
import sys
import re
from traceback import format_exc
from cStringIO import StringIO
from json import dumps
from inspect import getmembers, isfunction
import xbmc
import methods
from addon import Addon
from torrenter import Streamer, libtorrent, serve_file_from_torrent
from timers import Timer, check_seeding_limits, save_resume_data, log_torrents
from onscreen_label import OnScreenLabel
from utilities import get_mime

addon = Addon()

sys.path.append(os.path.join(addon.path, 'site-packages'))
from bottle import (route, default_app, request, template, response, debug,
                    static_file, TEMPLATE_PATH, HTTPError, HTTPResponse)

# Torrent client parameters
download_dir = addon.download_dir
resume_dir = os.path.join(addon.config_dir, 'torrents')
if not os.path.exists(resume_dir):
    os.mkdir(resume_dir)
# Initialize torrent client
torrent_client = Streamer(addon.torrent_port,
                          addon.torrent_port + 10,
                          addon.persistent,
                          resume_dir)
torrent_client.set_session_settings(download_rate_limit=addon.dl_speed_limit * 1024,
                                    upload_rate_limit=addon.ul_speed_limit * 1024,
                                    connections_limit=addon.connections_limit,
                                    half_open_limit=addon.half_open_limit,
                                    unchoke_slots_limit=addon.unchoke_slots_limit,
                                    connection_speed=addon.connection_speed,
                                    file_pool_size=addon.file_pool_size)
if not addon.enable_encryption:
    torrent_client.set_encryption_policy(2)
# Timers
if addon.enable_limits:
    limits_timer = Timer(10, check_seeding_limits, torrent_client)
if addon.persistent:
    save_resume_timer = Timer(30, save_resume_data, torrent_client)
log_torrents_timer = Timer(5, log_torrents, torrent_client)
# Bottle WSGI application
static_path = os.path.join(addon.path, 'resources', 'web')
TEMPLATE_PATH.insert(0, os.path.join(static_path, 'templates'))
debug(False)


@route('/')
def root():
    """
    Display a web-UI

    @return:
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
    Display brief JSON-RPC methods documentation

    @return:
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
    Process JSON-RPC requests

    @return:
    """
    addon.log('***** JSON request *****')
    addon.log(request.body.read())
    data = request.json
    reply = {'jsonrpc': '2.0', 'id': data.get('id', '1')}
    try:
        reply['result'] = getattr(methods, data['method'])(torrent_client, data.get('params'))
    except Exception, ex:
        addon.log(format_exc(), xbmc.LOGERROR)
        reply['error'] = '{0}: {1}'.format(str(ex.__class__)[7:-2], format_exc())
    addon.log('***** JSON response *****')
    addon.log(str(reply))
    return reply


@route('/torrents-json')
def get_torrents():
    """
    Get the list of available torrents with their params wrapped in JSON

    @return:
    """
    response.content_type = 'application/json'
    reply = dumps(torrent_client.get_all_torrents_info())
    # if DEBUG:
    #     addon.log(reply)
    return reply


@route('/static/<path:path>')
def get_static(path):
    """
    Serve static files

    @param path: relative path to a static file
    @return:
    """
    return static_file(path, root=static_path)


@route('/add-torrent/<source>', method='POST')
def add_torrent(source):
    """
    Add .torrent file or torrent link

    @param source: 'file' or 'link'
    @return:
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
def stream_file(path):
    """Stream torrent"""
    addon.log('********* Stream Torrent ***********')
    addon.log('Method: ' + request.method)
    addon.log('Headers: ' + str(request.headers.items()))
    if sys.platform == 'win32':
        path = path.decode('utf-8')
    file_path = os.path.normpath(os.path.join(download_dir, path))
    addon.log('File path: {0}'.format(file_path.encode('utf-8')))
    size = os.path.getsize(file_path)
    addon.log('File size: {0}'.format(size))
    mime = get_mime(file_path)
    headers = {'Content-Type': mime,
               'Content-Length': str(size),
               'Accept-Ranges': 'bytes'}
    response_status = 200
    if request.method == 'GET':
        range_match = re.search(r'^bytes=(\d*)-(\d*)$', request.get_header('Range'))
        start_pos = int(range_match.group(1) or 0)
        end_pos = int(range_match.group(2) or size - 1)
        addon.log('Getting requested range {0}-{1}'.format(start_pos, end_pos))
        if start_pos >= size or end_pos >= size:
            addon.log('Error 416, Requested Range Not Satisfiable')
            return HTTPError(416, 'Requested Range Not Satisfiable')
        response_status = 206
        headers['Content-Range'] = 'bytes {0}-{1}/{2}'.format(start_pos, end_pos, size)
        content_length = end_pos - start_pos + 1
        headers['Content-Length'] = str(content_length)
        streamed_file = torrent_client.streamed_file_data
        if (str(streamed_file['torr_handle'].status().state) == 'seeding'
            or content_length < streamed_file['piece_length'] * streamed_file['end_offset']):
            addon.log('Torrent is being seeded or the end piece requested.')
            # If the file is beeing seeded or Kodi checks the end piece,
            # then serve the file via Bottle.
            return static_file(path, root=download_dir, mimetype=get_mime(file_path))
        else:
            onscreen_label = OnScreenLabel('')
            start_piece = streamed_file['start_piece'] + start_pos / streamed_file['piece_length']
            addon.log('Start piece: {0}'.format(start_piece))
            addon.log('Streamed file: {0}'.format(str(streamed_file)))
            if start_pos > 0:
                addon.log('Resetting sliding window start to piece #{0}'.format(start_piece))
                # Set sliding window start 1 piece before the jump point to minimize (hopefully) image distortion.
                # Needs to be tested!
                torrent_client.start_sliding_window_async(streamed_file['torr_handle'],
                                                          start_piece - 1,
                                                          start_piece + addon.sliding_window_length - 1,
                                                          streamed_file['end_piece'] - streamed_file['end_offset'] - 1)
                # Wait until a specified number of pieces after a jump point are downloaded.
                end_piece = min(start_piece + streamed_file['buffer_length'], streamed_file['end_piece'])
                while not torrent_client.check_piece_range(streamed_file['torr_handle'], start_piece, end_piece):
                    percent = int(100 * float(torrent_client.sliding_window_position - start_piece + 1) /
                                  (end_piece - start_piece))
                    onscreen_label.text = addon.get_localized_string(32052).format(
                        percent,
                        streamed_file['torr_handle'].status().download_payload_rate / 1024)
                    onscreen_label.show()
                    xbmc.sleep(500)  # xbmc.sleep works better here
                onscreen_label.hide()
            addon.log('Starting file chunks serving...')
            body = serve_file_from_torrent(open(file_path, 'rb'),
                                           start_pos,
                                           streamed_file['torr_handle'],
                                           streamed_file['start_piece'],
                                           streamed_file['piece_length'],
                                           onscreen_label)
    else:
        body = ''
    addon.log('Reply headers: {0}'.format(str(headers)))
    return HTTPResponse(body, status=response_status, **headers)


app = default_app()
