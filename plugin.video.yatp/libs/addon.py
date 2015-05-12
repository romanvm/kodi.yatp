# -*- coding: utf-8 -*-
# Name:        utils
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcaddon


class Addon(xbmcaddon.Addon):
    """Helper class to access addon parameters"""
    def ui_string(self, string_id):
        """
        Return UI string by numeric ID
        :param string_id: int
        :return: srt
        """
        return self.getLocalizedString(string_id).encode('utf-8')

    def log(self, message):
        """
        Write message to the Kodi log
        for debuging purposes.
        """
        xbmc.log('{0}: {1}'.format(self.id, message.encode('utf-8')))

    @property
    def id(self):
        """
        Addon ID String
        :return: str
        """
        return self.getAddonInfo('id')

    @property
    def download_folder(self):
        """
        Save folder
        :return: str
        """
        return self.getSetting('download_folder')

    @property
    def keep_files(self):
        """
        Keep files after streaming
        :return: bool
        """
        return self.getSetting('keep_files') == 'true'

    @property
    def onscreen_info(self):
        """
        Show on-screen torrent info
        :return: bool
        """
        return self.getSetting('show_info') == 'true'
