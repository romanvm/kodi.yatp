# -*- coding: utf-8 -*-
# Name:        torrenter
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html

import platform
import os
import time
import threading

if platform.system() == 'Windows':
    from lt.win32 import libtorrent
else:
    raise RuntimeError('Your OS is not supported!')


class TorrenterError(Exception):
    """Custom exception"""
    pass


class AbortRequest(Exception):
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
        self._torrent_added = threading.Event()
        self._torrent = None  # Torrent handle for streamed torrent
        self._files = []

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
        for file_ in self.torrent.get_torrent_info().files():
            files.append(file_.path)
        return files

    def add_torrent(self, torrent, save_path):
        """
        Add torrent to the session
        :param torrent: str
        :param save_path: str
        :return:
        """
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
        self._torrent = torr_handle

    def add_torrent_async(self, torrent, save_path):
        """
        Add torrent asynchronously in a thread-safe way.
        :param torrent:
        :param save_path:
        :return:
        """
        self._thread_lock.acquire()
        self._torrent_added.clear()
        self.add_torrent(torrent, save_path)
        self._torrent_added.set()
        self._thread_lock.release()

    def remove_torrent(self, delete_files=False):
        """
        Delete streamed torrent
        :param delete_files: bool
        :return:
        """
        self._session.remove_torrent(self._torrent, delete_files)

