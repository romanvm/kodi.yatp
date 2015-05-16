# -*- coding: utf-8 -*-
# Name:        main
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import sys
import os
from urlparse import parse_qs
import xbmcgui
import xbmcplugin
from libs import player
from libs.addon import Addon


__addon__ = Addon()
__url__ = sys.argv[0]
__handle__ = int(sys.argv[1])


def plugin_root():
    """
    Plugin root section
    :return:
    """
    list_item = xbmcgui.ListItem(label='Select .torrent file to play...',
                                 iconImage=os.path.join(__addon__.icon_folder, 'torrent.png'),
                                 thumbnailImage=os.path.join(__addon__.icon_folder, 'torrent.png'))
    url = '{0}?action=select_torrent'.format(__url__)
    xbmcplugin.addDirectoryItem(handle=__handle__, url=url, listitem=list_item, isFolder=False)
    xbmcplugin.endOfDirectory(__handle__, True)


def select_torrent():
    """
    Select a torrent file to play
    :return:
    """
    torrent = xbmcgui.Dialog().browse(1, 'Select .torrent file to play', 'video', mask='.torrent')
    if torrent:
        __addon__.log('Torrent selected: {0}'.format(torrent))
        play_torrent(torrent, None)


def play_torrent(torrent, params):
    """
    Play torrent
    :param torrent:
    :return:
    """
    player.play_torrent(torrent, params, __addon__.download_folder, __addon__.keep_files, __addon__.onscreen_info)


def router(paramstring):
    """
    Router function
    :param paramstring: str
    :return:
    """
    params = parse_qs(paramstring)
    if params:
        if params['action'][0] == 'select_torrent':
            select_torrent()
        elif params['action'][0] == 'play':
            torrent = params['torrent'][0]
            __addon__.log('Torrent to play: {0}'.format(torrent))
            play_torrent(torrent, params)
    else:
        plugin_root()


if __name__ == '__main__':
    __addon__.log(str(sys.argv))
    try:
        router(sys.argv[2][1:])
    except KeyError as ex:
        xbmcgui.Dialog().notification('Error!', 'Invalid call parameters.', 'error', 3000)
        __addon__.log(ex.message)
