# coding: utf-8
# Module: onscreen_label
# Created on: 17.08.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html


import os
import xbmcgui
from xbmcaddon import Addon


class OnScreenLabel(object):
    def __init__(self, text=''):
        self._window = xbmcgui.Window(12005)
        self._back = xbmcgui.ControlImage(10, 20, 830, 60,
                                          os.path.join(Addon().getAddonInfo('path'),
                                                       'resources', 'icons',
                                                       'OverlayDialogBackground.png'))
        self._label = xbmcgui.ControlLabel(30, 35, 800, 50, text, textColor='0xFFFFFF00')
        self._is_added = False

    def _add_controls(self):
        self._window.addControl(self._back)
        self._window.addControl(self._label)
        self._is_added = True

    @property
    def text(self):
        return self._label.getLabel()

    @text.setter
    def text(self, value):
        self._label.setLabel(value)

    def show(self):
        if not self._is_added:
            # Controls are added when the label is shown for the 1st time.
            # This prevents showing a blank label on some systems.
            self._add_controls()
        self._back.setVisible(True)
        self._label.setVisible(True)

    def hide(self):
        self._back.setVisible(False)
        self._label.setVisible(False)
