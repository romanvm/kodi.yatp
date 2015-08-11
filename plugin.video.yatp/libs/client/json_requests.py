# coding: utf-8
# Module: json_requests
# Created on: 17.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
"""
JSON-RPC requests to the Torrent Server
"""

from requests import post
from simpleplugin import Addon

addon = Addon('plugin.video.yatp')
json_rpc_url = 'http://{0}:{1}/json-rpc'.format(addon.torrenter_host, addon.server_port)


def _request(data):
    """
    Send JSON-RPC request

    :param data:
    :return:
    """
    reply = post(json_rpc_url, json=data).json()
    try:
        return reply['result']
    except KeyError:
        raise RuntimeError(reply['error'])


def add_torrent(torrent):
    _request({'method': 'add_torrent', 'params': [torrent]})


def check_torrent_added():
    return _request({'method': 'check_torrent_added'})


def get_last_added_torrent():
    return _request({'method': 'get_last_added_torrent'})


def stream_torrent(info_hash, file_index, buffer_size):
    _request({'method': 'stream_torrent', 'params': [info_hash, file_index, buffer_size]})


def check_buffering_complete():
    return _request({'method': 'check_buffering_complete'})


def get_torrent_info(info_hash):
    return _request({'method': 'get_torrent_info', 'params': [info_hash]})


def abort_buffering():
    _request({'method': 'abort_buffering'})


def remove_torrent(info_hash, delete_files):
    _request({'method': 'remove_torrent', 'params': [info_hash, delete_files]})


def download_torrent(torrent, download_dir):
    _request({'method': 'add_torrent', 'params': [torrent, download_dir, False]})


def get_all_torrent_info():
    return _request({'method': 'get_all_torrent_info'})


def pause_torrent(info_hash):
    _request({'method': 'pause_torrent', 'params': [info_hash]})


def resume_torrent(info_hash):
    _request({'method': 'resume_torrent', 'params': [info_hash]})


def pause_all():
    _request({'method': 'pause_all'})


def resume_all():
    _request({'method': 'resume_all'})
