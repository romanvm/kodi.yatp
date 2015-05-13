# -*- coding: utf-8 -*-
# Name:        player
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import time
import xbmc
import xbmcgui
import xbmcvfs
from labels import TopLeftLabel
from streamer import Streamer


class TorrentPlayer(xbmc.Player):
    """
    Torrent Player class
    """
    pass


def play_torrent(torrent, dl_folder, keep_files=False, onscreen_info=False):
    """
    Play .torrent file or a magnet link
    :param torrent: str
    :return:
    """
    label = TopLeftLabel()
    trigger = True
    streamer = Streamer(dl_folder, keep_files)
    path = streamer.stream(torrent)
    if path is not None:
        player = TorrentPlayer()
        xbmcvfs.listdir(os.path.dirname(path))  # Magic function
        player.play(path)
        while player.isPlaying():
            time.sleep(0.5)
            if onscreen_info:
                label.text = \
'DL speed: {dl_speed}KB/s; UL speed: {ul_speed}KB/s; Total DL: {total_dl}MB; Total UL: {total_ul}MB; DL progress: {progress}%; Peers: {peers}'.format(
                dl_speed=streamer.dl_speed,
                ul_speed=streamer.ul_speed,
                total_dl=streamer.total_download,
                total_ul=streamer.total_upload,
                progress=streamer.progress,
                peers=streamer.num_peers
                )
            else:
                if streamer.is_seeding and trigger:
                    xbmcgui.Dialog.notification('Note', 'Torrent is completely downloaded.', 'info', 3000)
                    trigger = False
        label.hide()
        del label
        del streamer
