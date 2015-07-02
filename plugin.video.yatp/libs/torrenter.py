# -*- coding: utf-8 -*-
# Name:        torrenter
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import sys
import os
import time
import threading
from collections import deque

if sys.platform == 'win32':
    from lt.win32 import libtorrent
else:
    raise RuntimeError('Your OS is not supported!')


class TorrenterError(Exception):
    """Custom exception"""
    pass


class Torrenter(object):
    """The main Torrenter class"""
    def __init__(self, start_port=6681, end_port=6691):
        """
        Class constructor

        :param start_port: int
        :param end_port: int
        :return:
        """
        self._session = libtorrent.session()
        self._session.listen_on(start_port, end_port)
        self._session.start_dht()
        self._session.add_dht_router('router.bittorrent.com', 6881)
        self._session.add_dht_router('router.utorrent.com', 6881)
        self._session.add_dht_router('router.bitcomet.com', 6881)
        self._torrent_added = threading.Event()
        self._buffering_complete = threading.Event()
        self._abort_streaming = threading.Event()
        self._data_buffer = deque([0], maxlen=1)  # Thread-safe data buffer
        self._torrent = None  # Torrent handle for the streamed torrent

    def __del__(self):
        """Class destructor"""
        del self._session

    @property
    def torrent(self):
        """
        Get streamed torrent handle

        :return: object
        """
        return self._torrent

    @property
    def torrent_added(self):
        """
        Torrent added flag

        :return: bool
        """
        return self._torrent_added.is_set()

    @property
    def files(self):
        """
        The list of files in the torrent

        :return:
        """
        files = []
        if self.torrent is not None and self.torrent.is_valid():
            for file_ in self.torrent_info.files():
                files.append(file_.path)
        return files

    @property
    def buffering_complete(self):
        """
        Buffering complete flag

        :return: bool
        """
        return self._buffering_complete.is_set()

    @property
    def total_download(self):
        """
        Total download in MB

        :return: int
        """
        if self.torrent_status is not None:
            # total_done property holds correct volume of useful downloaded data.
            # total_payload_download returns incorrect value (with some overhead?)
            return int(self.torrent_status.total_done) / 1048576
        else:
            return 0

    @property
    def total_upload(self):
        """
        Total upload in MB

        :return: int
        """
        if self.torrent_status is not None:
            return int(self.torrent_status.total_payload_upload) / 1048576
        else:
            return 0

    @property
    def dl_speed(self):
        """
        DL speed in KB/s

        :return: int
        """
        if self.torrent_status is not None:
            return self.torrent_status.download_payload_rate / 1024
        else:
            return 0

    @property
    def ul_speed(self):
        """
        UL speed in KB/s

        :return: int
        """
        if self.torrent_status is not None:
            return self.torrent_status.upload_payload_rate / 1024
        else:
            return 0

    @property
    def num_peers(self):
        """
        The number of peers

        :return: int
        """
        if self.torrent_status is not None:
            return self.torrent_status.num_peers
        else:
            return 0

    @property
    def is_seeding(self):
        """
        Seeding status as bool

        :return: bool
        """
        if self.torrent_status is not None:
            return self.torrent_status.is_seeding
        else:
            return False

    @property
    def data_buffer(self):
        """
        Get data buffer contents

        :return:
        """
        return self._data_buffer[0]

    @property
    def torrent_status(self):
        """
        Get current torrent status

        :return:
        """
        try:
            return self._torrent.status()
        except AttributeError:
            return None

    @property
    def torrent_info(self):
        """
        Get current torrent info

        :return:
        """
        try:
            return self._torrent.get_torrent_info()
        except AttributeError:
            return None

    @property
    def torrent_progress(self):
        """
        Get torrent download progress in %

        :return:
        """
        try:
            return int(self.torrent_status.progress * 100)
        except AttributeError:
            return 0

    def add_torrent(self, torrent, save_path, zero_priorities=True):
        """
        Add torrent to the session

        :param torrent: str
        :param save_path: str
        :param zero_priorities: bool
        :return:
        """
        self._torrent_added.clear()
        if self.torrent is None or not self.torrent.is_valid():
            if torrent[:7] in ('magnet:', 'http://', 'https:/'):
                add_torrent_params = {'url': torrent}
            elif torrent[:7] == 'https:/':
                raise TorrenterError('HTTPS is not supported! For such links use external libraries, e.g. requests.')
            else:
                try:
                    add_torrent_params = {'ti': libtorrent.torrent_info(os.path.normpath(torrent))}
                except RuntimeError:
                    raise TorrenterError('Invalid path to the .torrent file!')
            add_torrent_params['save_path'] = save_path
            add_torrent_params['storage_mode'] = libtorrent.storage_mode_t.storage_mode_allocate
            torr_handle = self._session.add_torrent(add_torrent_params)
            while not torr_handle.has_metadata():  # Wait until torrent metadata are populated
                time.sleep(0.1)
            if zero_priorities:
                # Assign 0 priorities to all pieces to postpone download
                [torr_handle.piece_priority(i, 0) for i in xrange(torr_handle.get_torrent_info().num_pieces())]
            self._torrent = torr_handle
            self._torrent_added.set()
        else:
            raise TorrenterError('Torrenter already has a torrent!')

    def remove_torrent(self, delete_files=False):
        """
        Delete streamed torrent

        :param delete_files: bool
        :return:
        """
        if self._torrent is not None:
            self._session.remove_torrent(self._torrent, delete_files)
            self._torrent = None
        else:
            raise TorrenterError('Torrenter has no valid torrent!')

    def get_pieces_info(self, file_index):
        """
        Get the start piece and the number of pieces in the given file.

        Returns a tuple (start_piece, num_pieces)
        :param file_index: int
        :return: tuple
        """
        if self.torrent is not None and self.torrent.is_valid():
            # Pick the file to be streamed from the torrent files
            file_entry = self.torrent_info.files()[file_index]
            peer_req = self.torrent_info.map_file(file_index, 0, file_entry.size)
            # Start piece of the file
            start_piece = peer_req.piece
            # The number of pieces in the file
            num_pieces = peer_req.length / self.torrent_info.piece_length()
            return start_piece, num_pieces
        else:
            raise TorrenterError('Torrenter has no valid torrent!')

    def buffer_torrent(self, file_index, buffer_percent=5.0):
        """
        Buffer a videofile in torrent for playback

        :param file_index: int - file index in torrent
        :param buffer_percent: int - buffer size in %
        :return:
        """
        # Clear flags
        self._abort_streaming.clear()
        self._buffering_complete.clear()
        # Get pieces info
        start_piece, num_pieces = self.get_pieces_info(file_index)
        # The index of the end piece in the file
        end_piece = start_piece + num_pieces
        # The number of pieces at the start of the file
        # to be downloaded before the file can be played
        buffer_length = int(num_pieces * buffer_percent / 100.0)
        # Setup buffer download
        pieces_pool = range(start_piece, buffer_length + 1)
        pieces_pool.append(end_piece - 1)
        pieces_pool.append(end_piece)
        [self.torrent.piece_priority(piece, 1) for piece in pieces_pool]
        while len(pieces_pool) > 0:
            self._data_buffer.append(int(100 * (buffer_length + 3 - len(pieces_pool)) / (buffer_length + 3.0)))
            if self._abort_streaming.is_set():
                break
            for index, piece in enumerate(pieces_pool):
                if self.torrent.have_piece(piece):
                    del pieces_pool[index]
            time.sleep(0.1)
        else:
            self.torrent.flush_cache()
            self._buffering_complete.set()
            [self.torrent.piece_priority(piece, 1) for piece in xrange(start_piece + buffer_length + 1, end_piece - 1)]
            self.torrent.set_sequential_download()
        self._abort_streaming.clear()

    def abort_streaming(self):
        """
        Set abort streaming flag

        :return:
        """
        self._abort_streaming.set()

    def pause(self, graceful_pause=1):
        """
        Pause torrent

        :return:
        """
        self.torrent.pause(graceful_pause)

    def resume(self):
        """
        Resume torrent

        :return:
        """
        self.torrent.resume()
