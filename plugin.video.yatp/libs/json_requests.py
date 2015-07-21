# coding: utf-8
# Module: json_requests
# Created on: 17.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
"""
JSON-RPC requests to the Torrent Server
"""

from requests import post
from addon import Addon

json_rpc_url = Addon().torrenter_host + '/json-rpc'


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


def get_data_buffer():
    return _request({'method': 'get_data_buffer'})


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
