# -*- coding: utf-8 -*-
# Name:        tests
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
# The tests are not working!
# todo: implement tests.
import unittest
import os
import sys
import shutil
import time
import threading
import mock

__cwd__ = os.path.dirname(__file__)
sys.path.append(os.path.join(os.path.dirname(__cwd__), 'plugin.video.yatp'))
import libs.torrenter as torrenter
with mock.patch('sys.argv', ['plugin://plugin.video.yatp', '5', '']):
    import main

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
        self.torrenter.add_torrent(bbt_torrent_file, self.tempdir)
        self.torrenter.remove_torrent(True)
        time.sleep(0.5)  # Wait until the torrent is completely removed.
        self.assertTrue(self.torrenter.torrent is None)

    def test_adding_torrent_asynchronously(self):
        """
        Test adding torrent in a separate thread
        :return:
        """
        self.torrenter = torrenter.Torrenter()
        add_thread = threading.Thread(target=self.torrenter.add_torrent_async, args=(bbt_torrent_file, self.tempdir))
        add_thread.daemon = True
        add_thread.start()
        conut = 0
        while not self.torrenter.torrent_added:
            time.sleep(1.0)
            conut += 1
            if conut > 10:
                # Raise exception if the operation takes too long
                raise AssertionError('Max. waiting time exceeded!')
        self.assertEqual(str(self.torrenter.torrent.info_hash()), bbt_hash)

    def test_getting_pieces_info(self):
        """
        Test getting pieces info for a videofile
        :return:
        """
        filename = 'the.big.bang.theory.824.hdtv-lol.mp4'
        self.torrenter = torrenter.Torrenter()
        self.torrenter.add_torrent(bbt_torrent_file, self.tempdir)
        i = 0
        for file_ in self.torrenter.files:
            if filename in file_:
                break
            i += 1
        self.assertEqual(self.torrenter.get_pieces_info(i), (0, 466))

    @unittest.skip('Needs reworking')
    def test_streaming_torrent(self):
        """
        Test streaming torrent
        :return:
        """
        self.torrenter = torrenter.Torrenter()
        self.torrenter.add_torrent(bbt_torrent_file, self.tempdir)
        stream_theread = threading.Thread(target=self.torrenter.stream_torrent_async, args=(0, 1.0))
        stream_theread.daemon = True
        stream_theread.start()
        while not self.torrenter.buffering_complete:
            time.sleep(1.0)
            print 'Peers: {0}; DL speed: {1}KB/s; Downloaded: {2}MB'.format(
            self.torrenter.torrent.status().num_peers,
            self.torrenter.torrent.status().download_payload_rate / 1024,
            self.torrenter.torrent.status().total_done / 1048576)
        self.torrenter.pause()
        print 'Buffering complete!'
        assert True


class MainRouterTestCase(unittest.TestCase):
    """
    Test main.router function
    """
    @mock.patch('main.play_torrent')
    @mock.patch('main.select_torrent')
    @mock.patch('main.plugin_root')
    def test_router_function_with_different_paramstrings(self, mock_plugin_root, mock_select_torrent, mock_play_torrent):
        """
        Test router function with different paramstring
        :return:
        """
        main.router('')
        mock_plugin_root.assert_called_with()
        main.router('action=select_torrent')
        mock_select_torrent.assert_called_with()
        main.router('action=play&torrent=test')
        mock_play_torrent.assert_called_with('test')


if __name__ == '__main__':
    print 'Running tests. This may take some time.'
    unittest.main()
