# -*- coding: utf-8 -*-
# Name:        utils
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import xbmc
import xbmcaddon
import xbmcvfs


class Addon(xbmcaddon.Addon):
    """Helper class to access addon parameters"""
    def __init__(self):
        """Class constructor"""
        if self.getSetting('download_folder'):
            self._dl_folder = self.getSetting('download_folder')
        else:
            self._dl_folder = os.path.join(xbmc.translatePath('special://temp').decode('utf-8'), 'torrents')
        if not xbmcvfs.exists(self._dl_folder):
            xbmcvfs.mkdir(self._dl_folder)

    def ui_string(self, string_id):
        """
        Return UI string by numeric ID
        :param string_id: int
        :return: srt
        """
        return self.getLocalizedString(string_id).encode('utf-8')

    @staticmethod
    def log(message):
        """
        Write message to the Kodi log
        for debuging purposes.
        """
        xbmc.log('plugin.video.yatp: {0}'.format(message.encode('utf-8')))

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
        return self._dl_folder

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

    @property
    def addon_path(self):
        """
        Addon working folder
        :return: str
        """
        return self.getAddonInfo('path').decode('utf-8')

    @property
    def icon_folder(self):
        """
        Folders for icons
        :return:
        """
        return os.path.join(self.addon_path, 'resources', 'icons')
