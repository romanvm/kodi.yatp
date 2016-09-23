# -*- coding: utf-8 -*-
# Name:        utils
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Auxiliary module to access Kodi addon parameters
"""

import os
import sys
import xbmc
import simpleplugin


class Addon(simpleplugin.Addon):
    """Helper class to access addon parameters"""
    @property
    def credentials(self):
        return self.get_setting('web_login', False), self.get_setting('web_pass', False)

    @property
    def download_dir(self):
        d_dir = self.get_setting('download_dir') or xbmc.translatePath('special://temp')
        if sys.platform == 'win32':
            d_dir = d_dir.decode('utf-8')
        if not os.path.exists(d_dir):
            os.mkdir(d_dir)
        return d_dir
