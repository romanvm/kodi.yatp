# -*- coding: utf-8 -*-
# Name:        main
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import sys
import os
import time
from urlparse import parse_qs
import xbmc
import xbmcgui
import xbmcvfs
from libs.addon import Addon
from libs.player import TorrentPlayer
from libs.streamer import Streamer
from libs.labels import TopLeftLabel

__addon__ = Addon()


def play_torrent(torrent):
    """
    Play .torrent file or a magnet link
    :param torrent: str
    :return:
    """
    label = TopLeftLabel()
    trigger = True
    if xbmcvfs.exists(__addon__.download_folder):
        dl_folder = __addon__.download_folder
    else:
        dl_folder = os.path.join(xbmc.translatePath('special://temp').decode('utf-8'), 'torrents')
    streamer = Streamer(dl_folder, __addon__.keep_files)
    path = streamer.stream(torrent)
    if path is not None:
        player = TorrentPlayer()
        xbmcvfs.listdir(os.path.dirname(path))  # Magic function
        player.play(path)
        while player.isPlaying():
            time.sleep(0.5)
            if __addon__.onscreen_info:
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
                    xbmcgui.Dialog.notification(__addon__.id, 'Torrent is completely downloaded.', 'info', 3000)
                    trigger = False
        label.hide()
        del label
        del streamer


if __name__ == '__main__':
    params = parse_qs(sys.argv[2][1:])
    if params:
        try:
            play_torrent(params['torrent'][0])
        except KeyError:
            xbmcgui.Dialog().notification('Error!', 'Invalid call parameters.', 'error', 3000)
    else:
        torrent = xbmcgui.Dialog().browse(1, 'Select .torrent file to play', 'video', mask='.torrent')
        if torrent:
            play_torrent(torrent)
