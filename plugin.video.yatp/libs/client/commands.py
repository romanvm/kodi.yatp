# coding: utf-8
# Module: commands
# Created on: 28.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Context menu commands
"""

import sys
import xbmc
import xbmcgui
import json_requests as jsonrq
from xbmcaddon import Addon

addon = Addon('plugin.video.yatp')


def string(id_):
    return addon.getLocalizedString(id_).encode('utf-8')


def show_torrent_info(info_hash):
    """
    Display current torrent info

    :param info_hash:
    :return:
    """
    torr_info = jsonrq.get_torrent_info(info_hash)
    info_dialog = xbmcgui.DialogProgress()
    info_dialog.create(torr_info['name'])
    while not info_dialog.iscanceled():
        info_dialog.update(torr_info['progress'],
                           string(32011).format(torr_info['state'], torr_info['num_seeds'], torr_info['num_peers']),
                           string(32012).format(torr_info['size'], torr_info['dl_speed'], torr_info['ul_speed']),
                           string(32013).format(torr_info['total_download'], torr_info['total_upload']))
        xbmc.sleep(1000)
        torr_info = jsonrq.get_torrent_info(info_hash)


if __name__ == '__main__':
    if sys.argv[1] == 'pause':
        jsonrq.pause_torrent(sys.argv[2])
    elif sys.argv[1] == 'resume':
        jsonrq.resume_torrent(sys.argv[2])
    elif sys.argv[1] == 'delete' and xbmcgui.Dialog().yesno(string(32024), string(32025)):
        jsonrq.remove_torrent(sys.argv[2], False)
    elif sys.argv[1] == 'delete_with_files'and xbmcgui.Dialog().yesno(string(32024), string(32026), string(32027)):
        jsonrq.remove_torrent(sys.argv[2], True)
    elif sys.argv[1] == 'pause_all':
        jsonrq.pause_all()
    elif sys.argv[1] == 'resume_all':
        jsonrq.resume_all()
    elif sys.argv[1] == 'show_info':
        show_torrent_info(sys.argv[2])
    elif sys.argv[1] == 'restore_finished':
        jsonrq.restore_finished(sys.argv[2])
    else:
        raise RuntimeError('Invalid command: {0}!'.format(sys.argv[1]))
    xbmc.executebuiltin('Container.Refresh')
