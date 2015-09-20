# coding: utf-8
# Module: onscreen_label
# Created on: 17.08.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html


import os
import xbmcgui
from addon import Addon


class OnScreenLabel(object):
    def __init__(self, text='', visible=False):
        self._window = xbmcgui.Window(12005)
        self._back = xbmcgui.ControlImage(10, 150, 830, 60,
                                      os.path.join(Addon().path, 'resources', 'icons', 'OverlayDialogBackground.png'))
        self._window.addControl(self._back)
        self._label = xbmcgui.ControlLabel(30, 165, 800, 50, text, textColor='0xFFFFFF00')
        self._window.addControl(self._label)
        if not visible:
            self.hide()

    @property
    def text(self):
        return self._label.getLabel()

    @text.setter
    def text(self, value):
        self._label.setLabel(value)

    def show(self):
        self._back.setVisible(True)
        self._label.setVisible(True)

    def hide(self):
        self._back.setVisible(False)
        self._label.setVisible(False)
