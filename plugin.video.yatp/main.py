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
from libs import streamer
from libs.addon import Addon


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
    play_url = '{0}?action=select_torrent&then=play'.format(__url__)
    xbmcplugin.addDirectoryItem(handle=__handle__, url=play_url, listitem=play_item, isFolder=False)
    download_item = xbmcgui.ListItem(label='Downloadd torrent...',
                                     thumbnailImage=os.path.join(__addon__.icon_dir, 'download.png'),
                                     iconImage=os.path.join(__addon__.icon_dir, 'download.png'))
    download_url = '{0}?action=select_torrent&then=download'.format(__url__)
    xbmcplugin.addDirectoryItem(handle=__handle__, url=download_url, listitem=download_item, isFolder=False)
    xbmcplugin.endOfDirectory(__handle__)


def select_torrent(then):
    """
    Select a torrent file to play
    :return:
    """
    torrent = xbmcgui.Dialog().browse(1, 'Select .torrent file', 'video', mask='.torrent')
    if torrent:
        __addon__.log('Torrent selected: {0}'.format(torrent))
        if then == 'play':
            play_torrent(torrent)
        else:
            download_torrent(torrent)


def play_torrent(torrent, params=None):
    """
    Play torrent
    :param torrent:
    :return:
    """
    player.play_torrent(torrent, params, __addon__.download_dir, __addon__.keep_files, __addon__.onscreen_info)


def download_torrent(torrent, save_path=''):
    """
    Download torrent
    :param torrent: str
    :param save_path: str
    :return:
    """
    save_path = __addon__.download_dir if not save_path else save_path
    torrenter = streamer.Streamer(save_path, keep_files=True)
    torrenter.download_torrent(torrent)


def router(paramstring):
    """
    Router function
    :param paramstring: str
    :return:
    """
    params = dict(parse_qsl(paramstring[1:]))
    if params:
        if params['action'] == 'select_torrent':
            select_torrent(params['then'])
        elif params['action'] == 'play':
            torrent = urlsafe_b64decode(params['torrent'])
            __addon__.log('Torrent to play: {0}'.format(torrent))
            play_torrent(torrent, params)
        elif params['action'] == 'donwload':
            torrent = urlsafe_b64decode(params['torrent'])
            save_path = urlsafe_b64decode(params.get('save_path', ''))
            download_torrent(torrent, save_path)
        else:
            raise RuntimeError('Invalid action: {0}'.format(params['action']))
    else:
        plugin_root()


if __name__ == '__main__':
    __addon__.log(str(sys.argv))
    router(sys.argv[2])
