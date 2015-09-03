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


if __name__ == '__main__':
    if sys.argv[1] == 'pause':
        jsonrq.pause_torrent(sys.argv[2])
    elif sys.argv[1] == 'resume':
        jsonrq.resume_torrent(sys.argv[2])
    elif sys.argv[1] == 'delete':
        if xbmcgui.Dialog().yesno(string(32024), string(32025)):
            jsonrq.remove_torrent(sys.argv[2], False)
    elif sys.argv[1] == 'delete_with_files':
        if xbmcgui.Dialog().yesno(string(32024), string(32026), string(32027)):
            jsonrq.remove_torrent(sys.argv[2], True)
    elif sys.argv[1] == 'pause_all':
        jsonrq.pause_all()
    elif sys.argv[1] == 'resume_all':
        jsonrq.resume_all()
    xbmc.executebuiltin('Container.Refresh')
