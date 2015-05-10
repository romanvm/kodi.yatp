# -*- coding: utf-8 -*-
# Name:        utils
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import xbmc
import xbmcaddon


_addon = xbmcaddon.Addon()
_id = _addon.getAddonInfo('id')


def log(message):
    """
    Write message to the Kodi log
    for debuging purposes.
    """
    xbmc.log('{0}: {1}'.format(_id, message.encode('utf-8')))


def string(string_id):
    """
    Get language string by ID

    :param string_id: string
    :return: None
    """
    return _addon.getLocalizedString(string_id).encode('utf-8')
