# -*- coding: utf-8 -*-
# Name:        main
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Plugin main module
"""

import sys
import os
from urlparse import parse_qsl
#
import xbmcgui
import xbmcplugin
#
from libs.addon import Addon
from libs.streamer import buffer_torrent


__addon__ = Addon()
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])


def plugin_root():
    """
    Plugin root section

    :return:
    """
    play_item = xbmcgui.ListItem(label='Play .torrent file...',
                                 thumbnailImage=os.path.join(__addon__.icon_dir, 'play.png'),
                                 iconImage=os.path.join(__addon__.icon_dir, 'play.png'))
    play_url = '{0}?action=select_torrent'.format(__url__)
    play_item.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle=__handle__, url=play_url, listitem=play_item, isFolder=False)
    xbmcplugin.endOfDirectory(__handle__)


def select_torrent():
    """
    Select a torrent file to play

    :return:
    """
    torrent = xbmcgui.Dialog().browse(1, 'Select .torrent file', 'video', mask='.torrent')
    if torrent:
        __addon__.log('Torrent selected: {0}'.format(torrent))
        play_torrent(torrent)


def play_torrent(torrent):
    """
    Play torrent

    :param torrent:
    :return:
    """
    path = buffer_torrent(torrent)
    list_item = xbmcgui.ListItem(path=path)
    success = True if path else False
    xbmcplugin.setResolvedUrl(__handle__, success, list_item)


def router(paramstring):
    """
    Router function

    :param paramstring: str
    :return:
    """
    params = dict(parse_qsl(paramstring[1:]))
    if params:
        if params['action'] == 'select_torrent':
            select_torrent()
        elif params['action'] == 'play':
            torrent = params['torrent']
            __addon__.log('Torrent to play: {0}'.format(torrent))
            play_torrent(torrent)
        else:
            raise RuntimeError('Invalid action: {0}'.format(params['action']))
    else:
        plugin_root()


if __name__ == '__main__':
    __addon__.log(str(sys.argv))
    router(sys.argv[2])
