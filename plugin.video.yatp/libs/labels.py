# -*- coding: utf-8 -*-
# Module: messages
# Author: Roman V.M.
# Created on: 12.05.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import xbmcgui


class _ScreenLabel(object):
    """
    Base class for on-screen label
    """
    def __init__(self, color='0xFFFFFF00'):
        self._window = xbmcgui.Window(12005)
        self._label = xbmcgui.ControlLabel(-10, -10, 1, 1, '', textColor=color)
        self._window.addControl(self._label)

    @property
    def text(self):
        """
        Label text
        """
        return self._label.getLabel()

    @text.setter
    def text(self, text):
        self._label.setLabel(text)

    def show(self):
        """
        Show on-screen label
        """
        self._label.setVisible(True)

    def hide(self):
        """
        Hide on-screen label
        """
        self._label.setVisible(False)


class TopLeftLabel(_ScreenLabel):
    """
    Top Left label for torrent stats
    """
    def __init__(self, color='0x7FFFFF00'):
        super(TopLeftLabel, self).__init__(color)
        screen_width = self._window.getWidth()
        self._label.setPosition(10, 10)
        self._label.setWidth(screen_width - 20)
        self._label.setHeight(50)


class CentralLabel(_ScreenLabel):
    """
    Central label for "Buffering torrent..."
    """
    def __init__(self):
        super(CentralLabel, self).__init__()
        screen_width = self._window.getWidth()
        screen_height = self._window.getHeight()
        self._label.setPosition(screen_width / 2, screen_height / 2)
        self._label.setWidth(100)
        self._label.setHeight(25)
