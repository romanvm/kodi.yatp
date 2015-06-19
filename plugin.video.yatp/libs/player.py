# -*- coding: utf-8 -*-
# Name:        player
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import time
from base64 import urlsafe_b64decode
#
import xbmc
import xbmcgui
import xbmcvfs
#
from labels import TopLeftLabel
from streamer import Streamer
from addon import Addon

__addon__ = Addon()


def _add_params(list_item, params):
    """
    Add aditional parameters to list_item
    :param list_item: ListItem
    :param params: dict
    :return:
    """
    info = {}
    try:
        info['title'] = unicode(urlsafe_b64decode(params['title']), 'utf-8')
    except KeyError:
        pass
    try:
        info['season'] = int(params['season'])
    except (KeyError, ValueError):
        pass
    try:
        info['episode'] = int(params['episode'])
    except (KeyError, ValueError):
        pass
    thumb = unicode(urlsafe_b64decode(params.get('thumb', '')), 'utf-8')
    if thumb:
        list_item.setThumbnailImage(thumb)
        list_item.setIconImage(thumb)
    if info:
        list_item.setInfo('video', info)
    return list_item


def play_torrent(torrent, params, dl_folder, keep_files=False, onscreen_info=False):
    """
    Play .torrent file or a magnet link
    :param torrent: str
    :param params: dict
    :param dl_folder: str
    :param keep_files: bool
    :param onscreen_info: bool
    :return:
    """
    label = TopLeftLabel()
    trigger = True
    streamer = Streamer(dl_folder, keep_files)
    path = streamer.stream(torrent)
    if path is not None:
        player = xbmc.Player()
        xbmcvfs.listdir(os.path.dirname(path))  # Magic function - refresh a directory listing
        list_item = xbmcgui.ListItem(os.path.basename(path))
        if params is not None:
            list_item = _add_params(list_item, params)
        player.play(path, listitem=list_item)
        time.sleep(0.5)  # Needed to open a file with ListItem present, otherwise player.isPlaying() returns False
        while player.isPlaying():
            time.sleep(0.5)
            if onscreen_info:
                label.text = '; '.join(('DL speed: {0}KB/s'.format(streamer.dl_speed),
                                        'UL speed: {0}KB/s'.format(streamer.ul_speed),
                                        'Total DL: {0}MB'.format(streamer.total_download),
                                        'Total UL: {0}MB'.format(streamer.total_upload),
                                        'DL progress: {0}%'.format(streamer.file_progress),
                                        'Peers: {0}'.format(streamer.num_peers),
                                        ))
            else:
                if streamer.is_seeding and trigger:
                    xbmcgui.Dialog().notification(__addon__.id, 'Torrent is completely downloaded.',
                                                  __addon__.icon, 3000)
                    trigger = False
        label.hide()
        del label
        del streamer
