# coding: utf-8
# Module: actions
# Created on: 27.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)

import os
import time
import xbmcgui
from simpleplugin import Plugin
import json_requests as jsonrq
from commands import buffer_torrent

plugin = Plugin()
icons = os.path.join(plugin.path, 'resources', 'icons')
commands = os.path.join(os.path.dirname(__file__), 'commands.py')


def root(params):
    """
    Plugin root

    :param params:
    :return:
    """
    return [{'label': 'Play .torrent file...',
             'thumb': os.path.join(icons, 'play.png'),
             'url': plugin.get_url(action='select_torrent', target='play'),
             'is_playable': True},
            {'label': 'Download torrent from .torrent file...',
             'thumb': os.path.join(icons, 'download.png'),
             'url': plugin.get_url(action='select_torrent', target='download'),
             'is_folder': False}]


def select_torrent(params):
    """
    Select .torrent file to play

    :param params:
    :return:
    """
    torrent = xbmcgui.Dialog().browse(1, 'Select .torrent file', 'video', mask='.torrent')
    if torrent:
        plugin.log('Torrent selected: {0}'.format(torrent))
        if params['target'] == 'play':
            play_torrent({'torrent': torrent})
        else:
            download_torrent({'torrent': torrent})


def play_torrent(params):
    """
    Play torrent

    :param params:
    :return:
    """
    path = buffer_torrent(params['torrent'])
    success = True if path else False
    return plugin.resolve_url(path, success)


def download_torrent(params):
    """
    Add torrent for downloading

    :param params:
    :return:
    """
    download_dir = params.get('download_dir') or plugin.download_dir
    jsonrq.download_torrent(params['torrent'], download_dir)
    time.sleep(1.0)
    if jsonrq.check_torrent_added():
        xbmcgui.Dialog().notification('YATP', 'Torrent added for downloading', plugin.icon, 3000)


def torrents(params):
    """
    Display the list of torrents in the session

    :param params:
    :return:
    """
    listing = []
    torrent_list = jsonrq.get_all_torrent_info()
    for torrent in torrent_list:
        item = {'label': torrent['name'],
                'url': plugin.get_url(action='torrent_info', info_hash=torrent['info_hash']),
                'is_folder': False}
        listing.append(item)
    return listing


def torrent_info(params):
    """
    Display current torrent info

    :param params:
    :return:
    """
    torr_info = jsonrq.get_torrent_info(params['info_hash'])
    info_dialog = xbmcgui.DialogProgress()
    info_dialog.create(torr_info['name'])
    while not info_dialog.iscanceled():
        info_dialog.update(torr_info['progress'],
                           'size: {0}; state: {1}'.format(torr_info['size'], torr_info['state']),
                           'DL speed: {0}KB/s; UL speed: {1}KB/s'.format(torr_info['dl_speed'], torr_info['ul_speed']),
                           'total DL: {0}MB; total UL: {1}MB'.format(torr_info['total_download'],
                                                                     torr_info['total_upload']))
        time.sleep(1.0)
        torr_info = jsonrq.get_torrent_info(params['info_hash'])


plugin.actions['root'] = root
plugin.actions['select_torrent'] = select_torrent
plugin.actions['play'] = play_torrent
plugin.actions['download'] = download_torrent
plugin.actions['torrents'] = torrents
plugin.actions['torrent_info'] = torrent_info
