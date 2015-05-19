# -*- coding: utf-8 -*-
# Name:        main
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import sys
import os
from base64 import urlsafe_b64decode
from urlparse import parse_qsl
#
import xbmcgui
import xbmcplugin
#
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
    list_item = xbmcgui.ListItem(label='Select .torrent file to play...', thumbnailImage=os.path.join(__addon__.icon))
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
    player.play_torrent(torrent, params, __addon__.download_dir, __addon__.keep_files, __addon__.onscreen_info)


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
            torrent = urlsafe_b64decode(params['torrent'])
            __addon__.log('Torrent to play: {0}'.format(torrent))
            play_torrent(torrent, params)
        else:
            raise RuntimeError('Invalid action: {0}'.format(params['action']))
    else:
        plugin_root()


if __name__ == '__main__':
    __addon__.log(str(sys.argv))
    router(sys.argv[2])
