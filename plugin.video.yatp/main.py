# -*- coding: utf-8 -*-
# Name:        main
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import sys
from urlparse import parse_qs
import xbmcgui
from libs.player import play_torrent


if __name__ == '__main__':
    params = parse_qs(sys.argv[2][1:])
    if params:
        try:
            play_torrent(params['torrent'][0])
        except KeyError:
            xbmcgui.Dialog().notification('Error!', 'Invalid call parameters.', 'error', 3000)
    else:
        path = xbmcgui.Dialog().browse(2, 'Select .torrent file to play', 'video', mask='.torrent')
        if path:
            play_torrent(path)
