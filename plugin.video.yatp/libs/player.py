# -*- coding: utf-8 -*-
# Name:        player
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import time
import base64
#
import xbmc
import xbmcgui
import xbmcvfs
#
from labels import TopLeftLabel
from streamer import Streamer
from addon import Addon

__addon__ = Addon()


def add_params(list_item, params):
    """
    Add aditional parameters to list_item
    :param list_item: ListItem
    :param params: dict
    :return:
    """
    info = {}
    try:
        info['title'] = params['title']
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
    try:
        thumb = base64.urlsafe_b64decode(params['thumb'])
    except KeyError:
        thumb = ''
    if thumb:
        list_item.setThumbnailImage(thumb)
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
            list_item = add_params(list_item, params)
        player.play(path, listitem=list_item)
        time.sleep(0.5)  # Needed to open a file with ListItem present, otherwise player.isPlaying() returns False
        while player.isPlaying():
            time.sleep(0.5)
            if onscreen_info:
                label.text = \
'DL speed: {dl_speed}KB/s; UL speed: {ul_speed}KB/s; Total DL: {total_dl}MB; Total UL: {total_ul}MB; DL progress: {progress}%; Peers: {peers}'.format(
                dl_speed=streamer.dl_speed,
                ul_speed=streamer.ul_speed,
                total_dl=streamer.total_download,
                total_ul=streamer.total_upload,
                progress=streamer.file_progress,
                peers=streamer.num_peers
                )
            else:
                if streamer.is_seeding and trigger:
                    xbmcgui.Dialog().notification(__addon__.id, 'Torrent is completely downloaded.',
                                                  __addon__.icon, 3000)
                    trigger = False
        label.hide()
        del label
        del streamer
