# coding: utf-8
# Module: commands
# Created on: 28.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
"""
Context menu commands
"""

import sys
import xbmc
import xbmcgui
import json_requests as jsonrq

if __name__ == '__main__':
    if sys.argv[1] == 'pause':
        jsonrq.pause_torrent(sys.argv[2])
    elif sys.argv[1] == 'resume':
        jsonrq.resume_torrent(sys.argv[2])
    elif sys.argv[1] == 'delete':
        if xbmcgui.Dialog().yesno('Confirm delete', 'Do you really want to delete the torrent?'):
            jsonrq.remove_torrent(sys.argv[2], False)
    elif sys.argv[1] == 'delete_with_files':
        if xbmcgui.Dialog().yesno('Confirm delete',
                                  'Do you really want to delete the torrent with files?',
                                  'Warning: The files will be deleted permanently!'):
            jsonrq.remove_torrent(sys.argv[2], True)
    elif sys.argv[1] == 'pause_all':
        jsonrq.pause_all()
    elif sys.argv[1] == 'resume_all':
        jsonrq.resume_all()
    xbmc.executebuiltin('Container.Refresh')
