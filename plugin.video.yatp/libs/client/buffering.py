# -*- coding: utf-8 -*-
# Module: buffering
# Author: Roman V.M.
# Created on: 12.05.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html
"""
Buffering torrent
"""

import os
from time import sleep
from urllib import quote
import xbmcgui
import json_requests as jsonrq
from simpleplugin import Addon


addon = Addon()
string = addon.get_localized_string
media_url = addon.torrenter_host + '/media/'


def buffer_torrent(torrent):
    """
    Buffer a torrent and resolve a playable path from it

    :param torrent: str - magnet link or .torrent file URL
    :return:
    """
    jsonrq.add_torrent(torrent)
    progress_dialog = xbmcgui.DialogProgress()
    progress_dialog.create(string(32014))
    progress_dialog.update(0, string(32015), string(32016))
    while not (progress_dialog.iscanceled() or jsonrq.check_torrent_added()):
        sleep(1.0)
    if not progress_dialog.iscanceled():
        torrent_data = jsonrq.get_data_buffer()
        addon.log(str(torrent_data))
        # Create a list of videofiles in a torrent.
        # Each element is a tuple (<file name>, <file index in a torrent>).
        videofiles = []
        for file_index, file_ in enumerate(torrent_data['files']):
            if os.path.splitext(file_.lower())[1] in ('.avi', '.mkv', '.mp4', '.ts', '.m2ts', '.mov'):
                videofiles.append((file_index, os.path.basename(file_)))
        if videofiles:
            if len(videofiles) > 1:
                videofiles = sorted(videofiles, key=lambda i: i[1])
                index = xbmcgui.Dialog().select(string(32017), [item[1] for item in videofiles])
            else:
                index = 0
            if index >= 0:
                # Select a vileofile to play
                selected_file_index = videofiles[index][0]
                jsonrq.stream_torrent(torrent_data['info_hash'],
                                      selected_file_index,
                                      addon.buffer_size)
                while not (progress_dialog.iscanceled() or jsonrq.check_buffering_complete()):
                    buffer_progress = jsonrq.get_data_buffer()
                    torrent_info = jsonrq.get_torrent_info(torrent_data['info_hash'])
                    progress_dialog.update(buffer_progress,
                                           string(32018).format(torrent_info['total_download']),
                                           string(32019).format(torrent_info['dl_speed']),
                                           string(32020).format(torrent_info['num_seeds']))
                    sleep(1.0)
                if not progress_dialog.iscanceled():
                    progress_dialog.close()
                    return media_url + quote(torrent_data['files'][selected_file_index].replace('\\',
                                                                                                '/').encode('utf-8'))
                else:
                    jsonrq.abort_buffering()
                    if jsonrq.get_torrent_info(torrent_data['info_hash'])['state'] == 'downloading':
                        jsonrq.remove_torrent(torrent_data['info_hash'], True)
            else:
                xbmcgui.Dialog().notification(addon.id, string(32021), addon.icon, 3000)
        else:
            xbmcgui.Dialog().notification(addon.id, string(32022), 'error', 3000)
    if not (jsonrq.check_torrent_added() and jsonrq.check_buffering_complete()):
        xbmcgui.Dialog().notification(addon.id, string(32023), addon.icon, 3000)
    if not progress_dialog.iscanceled():
        progress_dialog.close()
    return ''
