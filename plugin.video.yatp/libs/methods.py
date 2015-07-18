# coding: utf-8
# Module: methods
# Created on: 02.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
"""JSON-RPC methdos implementation"""


def ping(torrenter, params=None):
    """
    Connection test method

    :return: 'pong'
    """
    return 'pong'


def add_torrent(torrenter, params):
    """
    Add torrent method

    The method calls add_torrent_async() in a separate thread
    and returns immediately. Then you need to poll torrent added status
    using check_torrent_added method.
    params[0] - str - magnet link or torrent URL
    params[1] - str - save path (optional).
        If save path is missing or equals an empty string then the default save path is used.
    params[2] - bool - zero priorities (do not start download immediately, optional, default - True)
    :return: 'OK'
    """
    torrenter.add_torrent_async(params[0], params[1], params[2])
    return 'OK'


def check_torrent_added(torrenter, params=None):
    """
    Check torrent_added flag

    params - None
    :return: bool - torrent added or not
    """
    return torrenter.torrent_added


def get_added_torrent_info(torrenter, params=None):
    """
    Get added torrent info

    params - None
    :return: dict - added torrent info
    """
    return torrenter.data_buffer


def get_torrent_info(torrenter, params):
    """
    Get torrent info

    params[0] - str - info_hash in lowercase
    :return: dict - extended torrent info
    """
    return torrenter.get_torrent_info(params[0])


def get_all_torrent_info(torrenter, params=None):
    """
    Get info for all torrents in the session

    :return: list - the list of torrent info dicts
    """
    return torrenter.get_all_torrents_info()


def pause_torrent(torrenter, params):
    """
    Pause torrent

    params[0] - torrent info-hash in lowercase
    :return: 'OK'
    """
    torrenter.pause_torrent(params[0])
    return 'OK'


def resume_torrent(torrenter, params):
    """
    Resume torrent

    params[0] - torrent info-hash in lowercase
    :return: 'OK'
    """
    torrenter.resume_torrent(params[0])
    return 'OK'


def remove_torrent(torrenter, params):
    """
    Remove torrent

    params[0] - info-hash
    params[1] - bool - also remove files
    :return: 'OK'
    """
    torrenter.remove_torrent(params[0], params[1])
    return 'OK'


def stream_torrent(torrenter, params):
    """
    Stream torrent

    params[0] - torrent info-hash in lowercase
    params[1] - the index of the file to be streamed
    params[2] - buffer size in % (default - 5.0%)
    :return: 'OK'
    """
    torrenter.stream_torrent_async(params[0], params[1], params[2])
    return 'OK'


def check_buffering_complete(torrenter, params=None):
    """
    Check if buffering is complete

    :return: bool - buffering status
    """
    return torrenter.buffering_complete


def abort_buffering(torrenter, params=None):
    """
    Abort buffering

    :return: 'OK'
    """
    torrenter.abort_buffering()
    return 'OK'


def get_data_buffer(torrenter, params=None):
    """
    Get torrenter data buffer contents

    :return: data buffer contents
    """
    return torrenter.data_buffer


def pause_all(torrenter, params=None):
    """
    Pause all torrents

    :return: 'OK'
    """
    torrenter.pause_all()
    return 'OK'


def resume_all(torrenter, params=None):
    """
    Resume all torrents

    :return: 'OK'
    """
    torrenter.resume_all()
    return 'OK'
