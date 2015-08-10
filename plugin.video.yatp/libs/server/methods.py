# coding: utf-8
# Module: methods
# Created on: 02.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
"""
JSON-RPC methods implementation

The methods are called via POST request at this address.
Don't forget to add ('Content-Type': 'application/json') header to your http-request.
The API is compliant with JSON-RPC 2.0, though 'jsonrpc' and 'id' keys are optional in requests.
Example:
{"method": "pause_torrent", "params": ["21df87c3cc3209e3b6011a88053aec35a58582a9"]}

"params" are an array (list) of method call parameters. Some methods do not take any parameters.
For those methods "params" key can be equal null or omitted at all.
"""


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
    return torrenter.is_torrent_added


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

    Note: The torrents are listed in random order,
    it us up to a client to sort the list accordingly.
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


def pause_group(torrenter, params):
    """
    Pause several torrents

    params[0] - the list of info-hashes in lowercase
    :return: 'OK'
    """
    for info_hash in params[0]:
        torrenter.pause_torrent(info_hash)
    return 'OK'


def resume_torrent(torrenter, params):
    """
    Resume torrent

    params[0] - torrent info-hash in lowercase
    :return: 'OK'
    """
    torrenter.resume_torrent(params[0])
    return 'OK'


def resume_group(torrenter, params):
    """
    Resume several torrents

    params[0] - the list of info-hashes in lowercase
    :return:
    """
    for info_hash in params[0]:
        torrenter.resume_torrent(info_hash)
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


def remove_group(torrenter, params):
    """

    params[0] - the list of info-hashes
    params[1] - bool - also remvove files
    :return:
    """
    for info_hash in params[0]:
        torrenter.remove_torrent(info_hash, params[1])
    return 'OK'


def stream_torrent(torrenter, params):
    """
    Stream torrent

    params[0] - torrent info-hash in lowercase
    params[1] - the index of the file to be streamed
    params[2] - buffer size in MB
    :return: 'OK'
    """
    torrenter.buffer_torrent_async(params[0], params[1], params[2])
    return 'OK'


def check_buffering_complete(torrenter, params=None):
    """
    Check if buffering is complete

    :return: bool - buffering status
    """
    return torrenter.is_buffering_complete


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
