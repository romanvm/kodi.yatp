# -*- coding: utf-8 -*-
# Name:        utils
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
#
import xbmc
import xbmcaddon
import xbmcvfs


class Addon(xbmcaddon.Addon):
    """Helper class to access addon parameters"""
    def __init__(self):
        """Class constructor"""
        self._configdir = xbmc.translatePath('special://profile/addon_data/{0}'.format(self.id)).decode('utf-8')
        if not os.path.exists(self._configdir):
            os.mkdir(self._configdir)
        if self.getSetting('download_folder'):
            self._dl_dir = self.getSetting('download_folder')
        else:
            self._dl_dir = os.path.join(xbmc.translatePath('special://temp').decode('utf-8'), 'torrents')
        if not xbmcvfs.exists(self._dl_dir):
            xbmcvfs.mkdir(self._dl_dir)

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
    def config_dir(self):
        """
        Addon config dir

        :return:
        """
        return self._configdir

    @property
    def download_dir(self):
        """
        Save folder
        :return: str
        """
        return self._dl_dir

    @property
    def path(self):
        """
        Addon working folder
        :return: str
        """
        return self.getAddonInfo('path').decode('utf-8')

    @property
    def icon(self):
        """
        Addon icon
        :return: str
        """
        return os.path.join(self.path, 'icon.png')

    @property
    def icon_dir(self):
        """
        Icons directory
        :return: str
        """
        return os.path.join(self.path, 'resources', 'icons')

    @property
    def buffer_size(self):
        """
        Buffer size in MB
        :return:
        """
        return int(self.getSetting('buffer_size'))

    @property
    def ratio_limit(self):
        """
        Seeding ratio limit

        :return:
        """
        return float(self.getSetting('ratio_limit'))

    @property
    def time_limit(self):
        """
        Seeding time limit

        :return:
        """
        return  int(self.getSetting('time_limit'))

    @property
    def torrenter_host(self):
        """
        Torrenter address

        :return:
        """
        return 'http://{0}:{1}'.format(self.getSetting('torrenter_host'), self.getSetting('server_port'))

    @property
    def expired_action(self):
        return self.getSetting('expired_action')

    @property
    def delete_expired_files(self):
        return self.getSetting('delete_expired_files') == 'true'

    @property
    def torrent_port(self):
        return int(self.getSetting('torrent_port'))

    @property
    def server_port(self):
        return int(self.getSetting('server_port'))
