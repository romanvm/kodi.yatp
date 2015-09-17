# coding: utf-8
# Module: json_requests
# Created on: 17.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
JSON-RPC requests to the Torrent Server
"""

from requests import post
from xbmcaddon import Addon

addon = Addon('plugin.video.yatp')
json_rpc_url = 'http://127.0.0.1:{0}/json-rpc'.format(addon.getSetting('server_port'))


def _request(data):
    """
    Send JSON-RPC request

    @param data: JSON request as dict
    @return:
    """
    reply = post(json_rpc_url, json=data).json()
    try:
        return reply['result']
    except KeyError:
        raise RuntimeError('JSON-RPC returned error:\n{0}'.format(reply['error']))


def add_torrent(torrent):
    _request({'method': 'add_torrent', 'params': {'torrent': torrent}})


def check_torrent_added():
    return _request({'method': 'check_torrent_added'})


def get_last_added_torrent():
    return _request({'method': 'get_last_added_torrent'})


def buffer_file(file_index):
    _request({'method': 'buffer_file', 'params': {'file_index': file_index}})


def check_buffering_complete():
    return _request({'method': 'check_buffering_complete'})


def get_torrent_info(info_hash):
    return _request({'method': 'get_torrent_info', 'params': {'info_hash': info_hash}})


def abort_buffering():
    _request({'method': 'abort_buffering'})


def remove_torrent(info_hash, delete_files):
    _request({'method': 'remove_torrent', 'params': {'info_hash': info_hash, 'delete_files': delete_files}})


def download_torrent(torrent, download_dir):
    _request({'method': 'add_torrent', 'params': {'torrent': torrent,
                                                  'save_path': download_dir,
                                                  'zero_priorities': False}})


def get_all_torrent_info():
    return _request({'method': 'get_all_torrent_info'})


def pause_torrent(info_hash):
    _request({'method': 'pause_torrent', 'params': {'info_hash': info_hash}})


def resume_torrent(info_hash):
    _request({'method': 'resume_torrent', 'params': {'info_hash': info_hash}})


def pause_all():
    _request({'method': 'pause_all'})


def resume_all():
    _request({'method': 'resume_all'})


def get_buffer_percent():
    return _request({'method': 'get_buffer_percent'})
