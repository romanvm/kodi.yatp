# coding: utf-8
# Module: actions
# Created on: 27.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)

import os
import xbmcgui
from simpleplugin import Plugin
from torrent_commands import buffer_torrent

plugin = Plugin()
icons = os.path.join(plugin.path, 'resources', 'icons')


def root(params):
    """
    Plugin root

    :param params:
    :return:
    """
    return [{'label': 'Play .torrent file...',
             'thumb': os.path.join(icons, 'play.png'),
             'url': plugin.get_url(action='select_torrent'),
             'is_playable': True}]


def select_torrent(params):
    """
    Select .torrent file to play

    :param params:
    :return:
    """
    torrent = xbmcgui.Dialog().browse(1, 'Select .torrent file', 'video', mask='.torrent')
    if torrent:
        plugin.log('Torrent selected: {0}'.format(torrent))
        play_torrent({'torrent': torrent})


def play_torrent(params):
    """
    Play torrent

    :param params:
    :return:
    """
    path = buffer_torrent(params['torrent'])
    success = True if path else False
    return plugin.resolve_url(path, success)


# Map actions
plugin.actions['root'] = root
plugin.actions['select_torrent'] = select_torrent
plugin.actions['play'] = play_torrent
