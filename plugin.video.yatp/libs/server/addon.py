# -*- coding: utf-8 -*-
# Name:        utils
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Auxiliary class to access Kodi addon parameters
"""

try:
    import simpleplugin
except ImportError:
    from standalone import ConfigParser
    Addon = ConfigParser
else:
    class Addon(simpleplugin.Addon):
        """Helper class to access addon parameters"""
        @property
        def credentials(self):
            return self.get_setting('web_login'), self.get_setting('web_pass')
