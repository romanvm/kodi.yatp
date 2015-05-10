# -*- coding: utf-8 -*-
# Name:        tests
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import unittest
import os
import sys
import shutil
import time

__cwd__ = os.path.dirname(__file__)
sys.path.append(os.path.join(__cwd__, 'plugin.video.yatp'))
import libs.torrenter as torrenter


class TorrenterTestCase(unittest.TestCase):
    """
    Test Torrenter class
    """
    def setUp(self):
        self.torrenter = None
        # "The Big Bang Theory S08E24 HDTV x264-LOL[ettv]" torrents
        self.torrent_file = 'http://torcache.net/torrent/1A16AFA4F2BCEB2D289F1E075E2BB08980C5D954.torrent?title=[kickass.to]the.big.bang.theory.s08e24.hdtv.x264.lol.ettv'
        self.magnet = 'magnet:?xt=urn:btih:1A16AFA4F2BCEB2D289F1E075E2BB08980C5D954&dn=the+big+bang+theory+s08e24+hdtv+x264+lol+ettv&tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce'
        self.tempdir = os.path.join(__cwd__, 'temp')
        os.mkdir(self.tempdir)

    def tearDown(self):
        del self.torrenter
        shutil.rmtree(self.tempdir, True)

    def test_adding_torrent_file_to_session(self):
        """
        Test adding .torrent file to session
        :return:
        """
        self.torrenter = torrenter.Torrenter()
        self.torrenter.add_torrent(self.torrent_file, self.tempdir)
        self.assertTrue(self.torrenter.torrent.is_valid())
        self.assertEqual(str(self.torrenter.torrent.info_hash()), '1a16afa4f2bceb2d289f1e075e2bb08980c5d954')

    def test_adding_magnet_link_to_session(self):
        """
        Test adding magnet link to session
        :return:
        """
        self.torrenter = torrenter.Torrenter()
        print '\nAdding magnet link...\nPlease wait.'
        self.torrenter.add_torrent(self.magnet, self.tempdir)
        self.assertTrue(self.torrenter.torrent.is_valid())
        self.assertEqual(str(self.torrenter.torrent.info_hash()), '1a16afa4f2bceb2d289f1e075e2bb08980c5d954')

    def test_removing_torrent_from_session(self):
        """
        Test removing torrent from session
        :return:
        """
        self.torrenter = torrenter.Torrenter()
        self.torrenter.add_torrent(self.torrent_file, self.tempdir)
        self.torrenter.remove_torrent(True)
        time.sleep(0.5)  # Wait until the torrent is completely removed.
        self.assertFalse(self.torrenter.torrent.is_valid())

if __name__ == '__main__':
    unittest.main()
