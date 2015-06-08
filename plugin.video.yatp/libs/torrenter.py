# -*- coding: utf-8 -*-
# Name:        torrenter
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import sys
import os
import time
import threading
from Queue import Queue

if sys.platform == 'win32':
    from lt.win32 import libtorrent
elif sys.platform == 'linux2':
    import libtorrent
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
        self._thread_lock = threading.Lock()
        self._data_buffer_lock = threading.Lock()
        self._torrent_added = threading.Event()
        self._buffering_complete = threading.Event()
        self._abort_streaming = threading.Event()
        self._data_buffer = Queue(1)  # Thread-safe data buffer
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
        self._data_buffer_lock.acquire()
        if self._data_buffer.full():
            contents = self._data_buffer.get_nowait()
        else:
            contents = None
        self._data_buffer_lock.release()
        return contents

    @data_buffer.setter
    def data_buffer(self, item):
        """
        Set data buffer contents
        :param item: item to put in the data buffer
        :return:
        """
        self._data_buffer_lock.acquire()
        if self._data_buffer.full():
            self._data_buffer.get_nowait()  # Clear data buffer
        self._data_buffer.put_nowait(item)
        self._data_buffer_lock.release()

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

    def add_torrent(self, torrent, save_path, zero_priorities=True):
        """
        Add torrent to the session

        :param torrent: str
        :param save_path: str
        :param zero_priorities: bool
        :return:
        """
        if self.torrent is None or not self.torrent.is_valid():
            if torrent[:7] in ('magnet:', 'http://', 'https:/'):
                add_torrent_params = {'url': torrent}
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
        else:
            raise TorrenterError('Torrenter already has a torrent!')

    def add_torrent_async(self, torrent, save_path, zero_priorities=True):
        """
        Add torrent asynchronously in a thread-safe way.
        :param torrent:
        :param save_path:
        :return:
        """
        self._thread_lock.acquire()
        self._torrent_added.clear()
        self.add_torrent(torrent, save_path, zero_priorities)
        self._torrent_added.set()
        self._thread_lock.release()

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

    def stream_torrent_async(self, file_index, buffer_percent=5.0):
        """
        Force sequential download of file for video playback.

        This is a simple implementation of a fixed size sliding window.
        This method should be run in a separate thread.
        If the streaming thread needs to be stopped before download is complete
        then set abort_streaming Event.
        Always terminate the streaming thread when existing the main program.
        use join() to wait until the thread terminates.
        :param file_index: int - the numerical index of the file to be streamed.
        :param buffer_percent: float - buffer size as % of the file size
        :return:
        """
        # Lock thread
        self._thread_lock.acquire()
        # Clear flags
        self._abort_streaming.clear()
        self._buffering_complete.clear()
        # Get pieces info
        start_piece, num_pieces = self.get_pieces_info(file_index)
        # The index of the end piece in the file
        end_piece = start_piece + num_pieces
        # The number of pieces at the start of the file
        # to be downloaded before the file can be played
        buffer_length = int(round(num_pieces * (buffer_percent / 100)))
        # Setup buffer download
        # Max priorities for the start and 2 end pieces.
        self.torrent.piece_priority(start_piece, 7)
        self.torrent.piece_priority(end_piece - 1, 7)
        self.torrent.piece_priority(end_piece, 7)
        # Set priorities for the playback buffer
        [self.torrent.piece_priority(i, 1) for i in xrange(start_piece + 1, start_piece + buffer_length + 1)]
        # Set up sliding window boundaries
        window_start = start_piece
        window_end = window_start + buffer_length
        # Loop until the end of the file
        while window_start < end_piece - 1:
            if self._abort_streaming.is_set():
                break  # Abort streaming by external request
            if self.torrent.have_piece(window_start):  # If the 1st piece in the window is downloaded...
                window_start += 1  # move window boundaries forward by 1 piece
                window_end += 1
                self.torrent.piece_priority(window_start, 7)
                if window_end < end_piece - 1:
                    self.torrent.piece_priority(window_end, 1)
            time.sleep(0.1)
            # Check if the buffer is downloaded completely
            if (not self._buffering_complete.is_set()
                    and window_start > start_piece + buffer_length
                    and self.torrent.have_piece(end_piece - 1)
                    and self.torrent.have_piece(end_piece)):
                self.torrent.flush_cache()
                self._buffering_complete.set()  # Set event if the buffer is downloaded
        self._abort_streaming.clear()
        self._thread_lock.release()

    def bufer_torrent_async(self, file_index, buffer_percent=5.0, offset=0):
        """
        Buffer torrent without further streaming

        :param file_index: int - the numerical index of the file to be streamed.
        :param buffer_percent: float - buffer size as % of the file size
        :param offset: int - starting piece
        :return:
        """
        # Lock thread
        self._thread_lock.acquire()
        # Clear flags
        self._abort_streaming.clear()
        self._buffering_complete.clear()
        # Get pieces info
        start_piece, num_pieces = self.get_pieces_info(file_index)
        start_piece += offset
        # The index of the end piece in the file
        end_piece = start_piece + num_pieces
        # The number of pieces at the start of the file
        # to be downloaded before the file can be played
        buffer_length = int(round(num_pieces * (buffer_percent / 100)))
        # Setup buffer download
        if start_piece + buffer_length <= end_piece - 2:
            buffer_end = start_piece + buffer_length
        else:
            buffer_end = end_piece - 2
        buffer_pieces = range(start_piece, buffer_end + 1)
        buffer_pieces.append(end_piece - 1)
        buffer_pieces.append(end_piece)
        # Set priorities for the playback buffer
        [self.torrent.piece_priority(i, 1) for i in buffer_pieces]
        # self.torrent.piece_priority(end_piece, 1)
        # Loop until buffer is downloaded
        while buffer_pieces:
            self.data_buffer = 100 * (buffer_length - len(buffer_pieces) + 3) / buffer_length
            if self._abort_streaming.is_set():
                break  # Abort streaming by external request
            time.sleep(0.5)
            for piece in buffer_pieces:
                if self._torrent.have_piece(piece):
                    del buffer_pieces[buffer_pieces.index(piece)]
        else:
            self.torrent.flush_cache()
            # Set normal download priority for all pieces
            [self.torrent.piece_priority(i, 1) for i in xrange(start_piece, start_piece + num_pieces)]
            self._buffering_complete.set()  # Set event if the buffer is downloaded
        self._abort_streaming.clear()
        self._thread_lock.release()

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
