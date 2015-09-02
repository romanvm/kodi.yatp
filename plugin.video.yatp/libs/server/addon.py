# -*- coding: utf-8 -*-
# Name:        utils
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Auxiliary module to access Kodi addon parameters
"""

import os
import xbmc
from libs import simpleplugin


class Addon(simpleplugin.Addon):
    """Helper class to access addon parameters"""
    def __init__(self):
        super(Addon, self).__init__()
        self._download_dir = (self.get_setting('download_dir') or
                              xbmc.translatePath('special://temp').decode('utf-8'))
        if not os.path.exists(self._download_dir):
            os.mkdir(self._download_dir)

    @property
    def credentials(self):
        return self.get_setting('web_login'), self.get_setting('web_pass')

    @property
    def download_dir(self):
        return self._download_dir
