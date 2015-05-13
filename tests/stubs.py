# -*- coding: utf-8 -*-
# Module: stubs
# Author: Roman V.M.
# Created on: 12.05.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html


class FakeDialog(object):
    """Fake Dialog Class"""
    def notification(self, *args, **kwargs):
        pass


class FakeDialogProgress(object):
    """Fake Dialog Progress Class"""
    def create(self, *args, **kwargs):
        pass

    def update(self, *args, **kwargs):
        pass

    def iscancelled(self):
        return False

    def close(self):
        pass


class FakePlayer(object):
    """
    Fake Player Class
    """
    pass
