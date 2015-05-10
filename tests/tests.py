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
import threading

__cwd__ = os.path.dirname(__file__)
sys.path.append(os.path.join(os.path.dirname(__cwd__), 'plugin.video.yatp'))
import libs.torrenter as torrenter

# The Big Bang Theory S08E24 HDTV x264-LOL[ettv].mp4
# Files: 3
# Total pieces: 467
# Duration: 1207s
bbt_torrent_file = 'http://torcache.net/torrent/1A16AFA4F2BCEB2D289F1E075E2BB08980C5D954.torrent?title=[kickass.to]the.big.bang.theory.s08e24.hdtv.x264.lol.ettv'
bbt_magnet = 'magnet:?xt=urn:btih:1A16AFA4F2BCEB2D289F1E075E2BB08980C5D954&dn=the+big+bang+theory+s08e24+hdtv+x264+lol+ettv&tr=udp%3A%2F%2Fopen.demonii.com%3A1337%2Fannounce'
bbt_hash = '1a16afa4f2bceb2d289f1e075e2bb08980c5d954'
# Game of Thrones S05E04 HDTV XviD-FUM.avi
# Files: 2
# Total pieces: 1698
# Duration 3021s
got_torrent_file = 'https://eztv.it/torrents/Game%20of%20Thrones%20S05E04%20HDTV%20XviD-FUM%20%5Beztv%5D.torrent'
got_magnet = 'magnet:?xt=urn:btih:55f98d6256b561112b9286ec5b2fdc78173474da&dn=Game%20of%20Thrones%20S05E04%20HDTV%20XviD-FUM%5Bettv%5D&tr=udp%3A%2F%2Ftracker.openbittorrent.com&tr=udp%3A%2F%2Ftracker.publicbt.com'
got_hash = '55f98d6256b561112b9286ec5b2fdc78173474da'


class TorrenterTestCase(unittest.TestCase):
    """
    Test Torrenter class
    """
    def setUp(self):
        self.torrenter = None
        # "The Big Bang Theory S08E24 HDTV x264-LOL[ettv]" torrents
        self.tempdir = os.path.join(__cwd__, 'temp')
        shutil.rmtree(self.tempdir, True)
        os.mkdir(self.tempdir)

    def tearDown(self):
        del self.torrenter
        shutil.rmtree(self.tempdir, True)

    def test_adding_torrent_file_to_session(self):
        """
        Test adding .torrent file to the session
        :return:
        """
        self.torrenter = torrenter.Torrenter()
        self.torrenter.add_torrent(bbt_torrent_file, self.tempdir)
        self.assertTrue(self.torrenter.torrent.is_valid())
        self.assertEqual(str(self.torrenter.torrent.info_hash()), bbt_hash)
        self.assertEqual(len(self.torrenter.files), 3)

    def test_adding_magnet_link_to_session(self):
        """
        Test adding magnet link to the session
        :return:
        """
        self.torrenter = torrenter.Torrenter()
        self.torrenter.add_torrent(bbt_magnet, self.tempdir)
        self.assertTrue(self.torrenter.torrent.is_valid())
        self.assertEqual(str(self.torrenter.torrent.info_hash()), bbt_hash)
        self.assertEqual(len(self.torrenter.files), 3)

    def test_removing_torrent_from_session(self):
        """
        Test removing torrent from the session
        :return:
        """
        self.torrenter = torrenter.Torrenter()
        self.torrenter.add_torrent(bbt_magnet, self.tempdir)
        self.torrenter.remove_torrent(True)
        time.sleep(0.5)  # Wait until the torrent is completely removed.
        self.assertFalse(self.torrenter.torrent.is_valid())

    def test_adding_torrent_asynchronously(self):
        """
        Test adding torrent in a separate thread
        :return:
        """
        self.torrenter = torrenter.Torrenter()
        thread_ = threading.Thread(target=self.torrenter.add_torrent_async, args=(bbt_torrent_file, self.tempdir))
        thread_.daemon = True
        thread_.start()
        time.sleep(3.0)  # Wait reasonable amount of time for the torrent to be added
        self.assertTrue(self.torrenter.torrent_added)
        self.assertEqual(str(self.torrenter.torrent.info_hash()), bbt_hash)


if __name__ == '__main__':
    unittest.main()
