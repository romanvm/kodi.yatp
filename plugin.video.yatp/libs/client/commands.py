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
from simpleplugin import Addon

addon = Addon('plugin.video.yatp')
_ = addon.initialize_gettext()


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
                           _('state: {0}; seeds: {1}; peers: {2}').format(
                               torr_info['state'],
                               torr_info['num_seeds'],
                               torr_info['num_peers']
                           ),
                           _('size: {0}MB; DL speed: {1}KB/s; UL speed: {2}KB/s').format(
                               torr_info['size'],
                               torr_info['dl_speed'],
                               torr_info['ul_speed']
                           ),
                           _('total DL: {0}MB; total UL: {1}MB').format(
                               torr_info['total_download'],
                               torr_info['total_upload'])
                           )
        xbmc.sleep(1000)
        torr_info = jsonrq.get_torrent_info(info_hash)


if __name__ == '__main__':
    if sys.argv[1] == 'pause':
        jsonrq.pause_torrent(sys.argv[2])
    elif sys.argv[1] == 'resume':
        jsonrq.resume_torrent(sys.argv[2])
    elif sys.argv[1] == 'delete' and xbmcgui.Dialog().yesno(
            _('Confirm delete'),
            _('Do you really want to delete the torrent?')):
        jsonrq.remove_torrent(sys.argv[2], False)
    elif sys.argv[1] == 'delete_with_files'and xbmcgui.Dialog().yesno(
            _('Confirm delete'),
            _('Do you really want to delete the torrent with files?'),
            _('Warning: The files will be deleted permanently!')):
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
        addon.log_debug('Command cancelled or invalid command: {0}'.format(sys.argv[1]))
    xbmc.executebuiltin('Container.Refresh')
