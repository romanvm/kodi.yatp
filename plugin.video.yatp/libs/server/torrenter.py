#!usr/bin/env python2
# -*- coding: utf-8 -*-
# Name:        torrenter
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  13.12.2014
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
The module implements a simple torrent client based on python-libtorrent library
with torrent media streaming capability.
"""

from __future__ import division
import os
import sys
import threading
import datetime
import platform
import cPickle as pickle
from math import ceil
from traceback import format_exc
from contextlib import closing
from requests import get
import xbmc
import xbmcvfs
from addon import Addon
from utilities import get_duration, HachoirError

kodi_monitor = xbmc.Monitor()
addon = Addon()
# This is for potential statistic and debugging purposes
addon.log('sys.platform: "{0}". platform.uname: "{1}"'.format(sys.platform, str(platform.uname())), xbmc.LOGNOTICE)

try:
    import libtorrent  # Try to import global module
except ImportError:
    sys.path.append(os.path.join(addon.path, 'site-packages'))
    from python_libtorrent import get_libtorrent
    libtorrent = get_libtorrent()

addon.log('libtorrent version: {0}'.format(libtorrent.version))


class TorrenterError(Exception):
    """Custom exception"""
    pass


class Buffer(object):
    """Thread-safe data buffer"""
    def __init__(self, contents=None):
        self._lock = threading.RLock()
        self._contents = contents

    @property
    def contents(self):
        """Get buffer contents"""
        with self._lock:
            return self._contents

    @contents.setter
    def contents(self, value):
        """Set buffer contents"""
        with self._lock:
            self._contents = value


class Torrenter(object):
    """
    Torrenter(start_port=6881, end_port=6891)

    Torrenter class

    Implements a simple torrent client.

    :param start_port: int
    :param end_port: int
    """
    def __init__(self, start_port=6881, end_port=6891):
        """
        Class constructor

        :param start_port: int
        :param end_port: int
        :return:
        """
        # torrents_pool is used to map torrent handles to their sha1 info_hashes (string hex digests)
        # Item format {info_hashes: torr_handle}
        self._torrents_pool = {}
        # Worker threads
        self._add_torrent_thread = None
        # Signal events
        self._torrent_added = threading.Event()
        # Inter-thread data buffer.
        self._last_added_torrent = Buffer()
        # Initialize session
        self._session = libtorrent.session(fingerprint=libtorrent.fingerprint('UT', 3, 4, 5, 41865))
        self._session.listen_on(start_port, end_port)
        self.set_session_settings(cache_size=256,  # 4MB
                                  ignore_limits_on_local_network=True,
                                  user_agent='uTorrent/3.4.5(41865)')
        self._session.add_dht_router('router.bittorrent.com', 6881)
        self._session.add_dht_router('router.utorrent.com', 6881)
        self._session.add_dht_router('router.bitcomet.com', 6881)
        self._session.start_dht()
        self._session.start_lsd()
        self._session.start_upnp()
        self._session.start_natpmp()

    def __del__(self):
        """
        Class destructor

        Always delete the Torrenter instance when
        exiting the main program.
        """
        try:
            self._add_torrent_thread.join()
        except (RuntimeError, AttributeError):
            pass
        del self._session

    def set_encryption_policy(self, enc_policy=1):
        """
        Set encryption policy for the session

        :param enc_policy: int - 0 = forced, 1 = enabled, 2 = disabled
        :return:
        """
        pe_settings = self._session.get_pe_settings()
        pe_settings.in_enc_policy = pe_settings.out_enc_policy = libtorrent.enc_policy(enc_policy)
        self._session.set_pe_settings(pe_settings)

    def set_session_settings(self, **settings):
        """
        Set session settings.

        See `libtorrent API docs`_ for more info.

        :param settings: session settings key=value pairs
        :return:

        .. _libtorrent API docs: http://www.rasterbar.com/products/libtorrent/manual.html#session-customization
        """
        ses_settings = self._session.get_settings()
        for key, value in settings.iteritems():
            ses_settings[key] = value
        self._session.set_settings(ses_settings)

    def add_torrent_async(self, torrent, save_path, paused=False, cookies=None):
        """
        Add a torrent in a non-blocking way.

        This method will add a torrent in a separate thread. After calling the method,
        the caller should periodically check is_torrent_added flag and, when
        the flag is set, retrieve results from last_added_torrent.

        :param torrent: str - path to a .torrent file or a magnet link
        :param save_path: str - save path
        :param paused: bool
        :param cookies: dict
        :return:
        """
        self._add_torrent_thread = threading.Thread(target=self.add_torrent,
                                                    args=(torrent, save_path, paused, cookies))
        self._add_torrent_thread.daemon = True
        self._add_torrent_thread.start()

    def add_torrent(self, torrent, save_path, paused=False, cookies=None):
        """
        Add a torrent download

        :param torrent: str
        :param save_path: str
        :param paused: bool
        :param cookies: dict
        :return:
        """
        self._torrent_added.clear()
        torr_handle = self._add_torrent(torrent, save_path, cookies=cookies)
        info_hash = str(torr_handle.info_hash())
        self._last_added_torrent.contents = {
            'name': torr_handle.name().decode('utf-8'),
            'info_hash': info_hash,
            'files': self.get_files(info_hash)
        }
        if paused:
            self.pause_torrent(info_hash)  # Tested variant. Other variants don't work with 1.x.x
        self._torrent_added.set()

    def _add_torrent(self, torrent, save_path, resume_data=None, cookies=None):
        """
        Add a torrent to the pool.

        :param torrent: str - the path to a .torrent file or a magnet link
        :param save_path: str - torrent save path
        :param resume_data: str - bencoded torrent resume data
        :return: object - torr_handle
        """
        add_torrent_params = {'save_path': os.path.abspath(save_path),
                              'storage_mode': libtorrent.storage_mode_t.storage_mode_sparse}
        if resume_data is not None:
            add_torrent_params['resume_data'] = resume_data
        if isinstance(torrent, dict):
            add_torrent_params['ti'] = libtorrent.torrent_info(torrent)
        elif torrent[:7] == 'magnet:':
            add_torrent_params['url'] = str(torrent)  # libtorrent doesn't like unicode objects here
        elif torrent[:7] in ('http://', 'https:/'):
            # Here external http/https client is used in case if libtorrent module is compiled without OpenSSL
            torr_file = get(torrent, cookies=cookies, verify=False).content
            add_torrent_params['ti'] = libtorrent.torrent_info(libtorrent.bdecode(torr_file))
        else:
            try:
                with closing(xbmcvfs.File(torrent)) as file_obj:
                    add_torrent_params['ti'] = libtorrent.torrent_info(libtorrent.bdecode(file_obj.read()))
            except:
                addon.log(format_exc(), xbmc.LOGERROR)
                raise TorrenterError('Error when adding torrent: {0}!'.format(torrent))
        torr_handle = self._session.add_torrent(add_torrent_params)
        while not torr_handle.has_metadata():  # Wait until torrent metadata are populated
            xbmc.sleep(100)
        torr_handle.auto_managed(False)
        self._torrents_pool[str(torr_handle.info_hash())] = torr_handle
        return torr_handle

    def _get_torrent_status(self, info_hash):
        """
        Get torrent status

        :param info_hash: str
        :return: object status
        """
        try:
            torr_handle = self._torrents_pool[info_hash]
        except KeyError:
            raise TorrenterError('Invalid torrent hash!')
        if torr_handle.is_valid():
            return torr_handle.status()
        return None

    def _get_torrent_info(self, info_hash):
        """
        Get torrent info

        :param info_hash: str
        :return: object torrent_info
        """
        try:
            torr_handle = self._torrents_pool[info_hash]
        except KeyError:
            raise TorrenterError('Invalid torrent hash!')
        if torr_handle.is_valid():
            return torr_handle.get_torrent_info()
        return None

    def remove_torrent(self, info_hash, delete_files=False):
        """
        Remove a torrent from download

        :param info_hash: str
        :return:
        """
        try:
            self._session.remove_torrent(self._torrents_pool[info_hash], delete_files)
        except KeyError:
            raise TorrenterError('Invalid torrent hash!')

    def pause_torrent(self, info_hash, graceful_pause=1):
        """
        Pause a torrent

        :param info_hash: str
        :return:
        """
        try:
            self._torrents_pool[info_hash].pause(graceful_pause)
        except KeyError:
            raise TorrenterError('Invalid torrent hash!')

    def resume_torrent(self, info_hash):
        """
        Resume a torrent

        :param info_hash: str
        :return:
        """
        try:
            self._torrents_pool[info_hash].resume()
        except KeyError:
            raise TorrenterError('Invalid torrent hash!')

    def get_torrent_info(self, info_hash):
        """
        Get torrent info in a human-readable format

        The following info is returned::

            name - torrent's name
            size - MB
            state - torrent's current state
            dl_speed - KB/s
            ul_speed - KB/s
            total_download - MB
            total_upload - MB
            progress - int %
            num_peers
            num_seeds
            added_time - timestamp in 'YYYY-MM-DD HH:MM:SS' format
            completed_time - see above
            info_hash - torrent's info_hash hexdigest in lowecase

        :param info_hash: str
        :return: dict - torrent info or None for invalid torrent
        """
        torr_info = self._get_torrent_info(info_hash)
        torr_status = self._get_torrent_status(info_hash)
        state = str(torr_status.state)
        if torr_status.paused:
            state = 'paused'
        elif state == 'finished':
            state = 'incomplete'
        if torr_info is None or torr_status is None:
            return None
        completed_time = str(datetime.datetime.fromtimestamp(int(torr_status.completed_time)))
        return {'name': torr_info.name().decode('utf-8'),
                'size': int(torr_info.total_size() / 1048576),
                'state': state,
                'progress': int(torr_status.progress * 100),
                'dl_speed': int(torr_status.download_payload_rate / 1024),
                'ul_speed': int(torr_status.upload_payload_rate / 1024),
                'total_download': int(torr_status.total_done / 1048576),
                'total_upload': int(torr_status.total_payload_upload / 1048576),
                'num_seeds': torr_status.num_seeds,
                'num_peers': torr_status.num_peers,
                 # Timestamp in 'YYYY-MM-DD HH:MM:SS' format
                'added_time': str(datetime.datetime.fromtimestamp(int(torr_status.added_time))),
                'completed_time': completed_time if completed_time[:10] != '1970-01-01' else '-',
                'info_hash': info_hash}

    def get_all_torrents_info(self):
        """
        Get info for all torrents in the session

        Note that the torrents info list will have a random order.
        It is up to the caller to sort the list accordingly.

        :return: list - the list of torrent info dicts
        """
        listing = []
        for info_hash in self._torrents_pool.iterkeys():
            torrent_info = self.get_torrent_info(info_hash)
            if torrent_info is not None:
                listing.append(torrent_info)
        return listing

    def pause_all(self, graceful_pause=1):
        """
        Pause all torrents

        :return:
        """
        for info_hash in self._torrents_pool.iterkeys():
            self.pause_torrent(info_hash, graceful_pause)

    def resume_all(self):
        """
        Resume all torrents

        :return:
        """
        for info_hash in self._torrents_pool.iterkeys():
            self.resume_torrent(info_hash)

    def prioritize_file(self, info_hash, file_index, priority):
        """
        Prioritize a file in a torrent

        If all piece priorities in the torrent are set to 0, to enable downloading an individual file
        priority value must be no less than 2.

        :param info_hash: str - torrent info-hash
        :param file_index: int - the index of a file in the torrent
        :param priority: int - priority from 0 to 7.
        :return:
        """
        self._torrents_pool[info_hash].file_priority(file_index, priority)

    def set_piece_priorities(self, info_hash, priority=1):
        """
        Set priorities for all pieces in a torrent

        :param info_hash: str
        :param priority: int
        :return:
        """
        torr_handle = self._torrents_pool[info_hash]
        [torr_handle.piece_priority(piece, priority) for piece in xrange(torr_handle.get_torrent_info().num_pieces())]

    def get_files(self, info_hash):
        """
        Get the list of videofiles in a torrent

        :param info_hash:
        :return: a list of tuples (path, size)
        """
        file_storage = self._get_torrent_info(info_hash).files()
        if libtorrent.version < '1.1.0':
            return [(file_.path.decode('utf-8'), file_.size) for file_ in file_storage]
        else:
            return [(file_storage.file_path(i), file_storage.file_size(i))
                    for i in xrange(file_storage.num_files())]

    @property
    def is_torrent_added(self):
        """Torrent added flag"""
        return self._torrent_added.is_set()

    @property
    def last_added_torrent(self):
        """The last added torrent info"""
        return self._last_added_torrent.contents


class TorrenterPersistent(Torrenter):
    """
    TorrenterPersistent(start_port=6881, end_port=6891, persistent=False, resume_dir='')

    A persistent version of Torrenter

    It stores the session state and torrents data on disk

    :param start_port: int
    :param end_port: int
    :param persistent: bool - store persistent torrent data on disk
    :param resume_dir: str - the directory to store persistent torrent data
    """
    def __init__(self, start_port=6881, end_port=6891, persistent=False, resume_dir=''):
        """
        Class constructor

        :param start_port: int
        :param end_port: int
        :param persistent: bool - store persistent torrent data on disk
        :param resume_dir: str - the directory to store persistent torrent data
        :return:
        """
        super(TorrenterPersistent, self).__init__(start_port, end_port)
        # Use persistent storage for session and torrents info
        self._persistent = persistent
        # The directory where session and torrent data are stored
        self._resume_dir = os.path.abspath(resume_dir)
        if self._persistent:
            try:
                self._load_session_state()
            except TorrenterError:
                self._save_session_state()
            self._load_torrents()

    def __del__(self):
        """Class destructor"""
        if self._persistent:
            self.save_all_resume_data()
        super(TorrenterPersistent, self).__del__()

    def add_torrent(self, torrent, save_path, paused=False, cookies=None):
        """
        Add a torrent download

        :param torrent: str
        :param save_path: str
        :param paused: bool
        :param cookies: dict
        :return:
        """
        super(TorrenterPersistent, self).add_torrent(torrent, save_path, paused, cookies)
        if self._persistent:
            self._save_torrent_info(self._torrents_pool[self._last_added_torrent.contents['info_hash']])

    def _save_session_state(self):
        """
        Save session state

        :return:
        """
        if self._persistent:
            with open(os.path.join(self._resume_dir, 'session.state'), mode='wb') as state_file:
                pickle.dump(self._session.save_state(), state_file)
        else:
            raise TorrenterError('Trying to save the state of a non-persistent instance!')

    def _load_session_state(self):
        """
        Load session state

        :return:
        """
        try:
            with open(os.path.join(self._resume_dir, 'session.state'), mode='rb') as state_file:
                self._session.load_state(pickle.load(state_file))
        except IOError:
            raise TorrenterError('.state file not found!')

    def _save_resume_data(self, info_hash, force_save=False):
        """
        Save fast-resume data for a torrent.

        :param info_hash: str
        :return:
        """
        if self._persistent:
            torrent_handle = self._torrents_pool[info_hash]
            if torrent_handle.need_save_resume_data() or force_save:
                resume_data = libtorrent.bencode(torrent_handle.write_resume_data())
                with open(os.path.join(self._resume_dir, info_hash + '.resume'), mode='r+b') as meta_file:
                    metadata = pickle.load(meta_file)
                    metadata['resume_data'] = resume_data
                    meta_file.seek(0)
                    pickle.dump(metadata, meta_file)
                    meta_file.truncate()
        else:
            raise TorrenterError('Trying to save torrent metadata for a non-persistent instance!')

    def save_all_resume_data(self, force_save=False):
        """
        Save fast-resume data for all torrents

        :return:
        """
        if self._persistent:
            for key in self._torrents_pool.iterkeys():
                self._save_resume_data(key, force_save)
            self._session.save_state()
        else:
            raise TorrenterError('Trying to save torrent metadata for a non-persistent instance!')

    def _save_torrent_info(self, torr_handle):
        """
        Save torrent metatata and a .torrent file for resume.

        :param torr_handle: object - torrent handle
        :return:
        """
        if self._persistent:
            info_hash = str(torr_handle.info_hash())
            torr_filepath = os.path.join(self._resume_dir, info_hash + '.torrent')
            meta_filepath = os.path.join(self._resume_dir, info_hash + '.resume')
            torr_info = torr_handle.get_torrent_info()
            torr_file = libtorrent.create_torrent(torr_info)
            torr_content = torr_file.generate()
            torr_bencoded = libtorrent.bencode(torr_content)
            with open(torr_filepath, 'wb') as t_file:
                t_file.write(torr_bencoded)
            metadata = {'name': torr_handle.name(),
                        'info_hash': info_hash,
                        'save_path': torr_handle.save_path(),
                        'resume_data': None}
            with open(meta_filepath, mode='wb') as m_file:
                pickle.dump(metadata, m_file)
        else:
            raise TorrenterError('Trying to save torrent metadata for a non-persistent instance!')

    def _load_torrent_info(self, filepath):
        """
        Load torrent state from a pickle file and add the torrent to the pool.

        :param filepath: str
        :return:
        """
        try:
            with open(filepath, mode='rb') as m_file:
                metadata = pickle.load(m_file)
        except (IOError, EOFError, ValueError, pickle.PickleError):
            addon.log('Resume file "{0}" is missing or corrupted!'.format(filepath), xbmc.LOGERROR)
        else:
            torrent = os.path.join(self._resume_dir, metadata['info_hash'] + '.torrent')
            self._add_torrent(torrent, metadata['save_path'], metadata['resume_data'])

    def _load_torrents(self):
        """
        Load all torrents

        :return:
        """
        dir_listing = os.listdir(self._resume_dir)
        for item in dir_listing:
            if item[-7:] == '.resume':
                self._load_torrent_info(os.path.join(self._resume_dir, item))

    def remove_torrent(self, info_hash, delete_files=False):
        """
        Remove a torrent from download

        :param info_hash: str
        :return:
        """
        super(TorrenterPersistent, self).remove_torrent(info_hash, delete_files)
        if self._persistent:
            try:
                os.remove(os.path.join(self._resume_dir, info_hash + '.resume'))
                os.remove(os.path.join(self._resume_dir, info_hash + '.torrent'))
            except OSError:
                raise TorrenterError('Info files not found!')


class Streamer(TorrenterPersistent):
    """
    Streamer(start_port=6881, end_port=6891, persistent=False, resume_dir='')

    Torrent Streamer class

    Implements a torrent client with media streaming capability

    :param start_port: int
    :param end_port: int
    :param persistent: bool - store persistent torrent data on disk
    :param resume_dir: str - the directory to store persistent torrent data
    """
    def __init__(self, *args, **kwargs):
        """Class constructor"""
        # Worker threads
        self._buffer_file_thread = None
        self._sliding_window_thread = None
        # Signal events
        self._buffering_complete = threading.Event()
        self._abort_buffering = threading.Event()
        self._abort_sliding = threading.Event()
        # Inter-thread data buffers
        self._buffer_percent = Buffer(0)
        self._streamed_file_data = Buffer()
        self._sliding_window_position = Buffer(-1)
        super(Streamer, self).__init__(*args, **kwargs)

    def __del__(self):
        """Class destructor"""
        self.abort_buffering()
        super(Streamer, self).__del__()

    def buffer_file_async(self, file_index, buffer_duration, sliding_window_length, default_buffer_size,
                          info_hash=None):
        """
        Force sequential download of file for video playback.

        This method will stream a torrent in a separate thread. The caller should periodically
        check buffering_complete flag. If buffering needs to be terminated,
        the caller should call abort_buffering method.

        .. warning:: The torrent must be already added via add_torrent method!

        :param file_index: int - the numerical index of the file to be streamed.
        :param buffer_duration: int - buffer duration in s
        :param sliding_window_length: int - the length of a sliding window in pieces
        :param default_buffer_size: int - fallback buffer size if a video cannot be parsed by hachoir
        :param info_hash: torrent's info-hash (optional)
        :return:
        """
        self._buffer_file_thread = threading.Thread(target=self._buffer_file, args=(file_index,
                                                                                    buffer_duration,
                                                                                    sliding_window_length,
                                                                                    default_buffer_size,
                                                                                    info_hash))
        self._buffer_file_thread.daemon = True
        self._buffer_file_thread.start()

    def _buffer_file(self, file_index, buffer_duration, sliding_window_length, default_buffer_size, info_hash=None):
        """
        Force sequential download of file for video playback.

        .. warning:: The torrent must be already added via add_torrent method!

        :param file_index: int - the numerical index of the file to be streamed.
        :param buffer_duration: int - buffer duration in s
        :param sliding_window_length: int - the length of a sliding window in pieces
        :param default_buffer_size: int - fallback buffer size if a video cannot be parsed by hachoir
        :param info_hash: torrent's info-hash (optional)
        :return:
        """
        if info_hash is None:
            info_hash = self.last_added_torrent['info_hash']
        files = self.get_files(info_hash)
        if file_index not in range(len(files)):
            raise IndexError('Invalid file index: {0}!'.format(file_index))
        # Clear flags
        self._buffering_complete.clear()
        self._abort_buffering.clear()
        self._buffer_percent.contents = 0
        torr_handle = self._torrents_pool[info_hash]
        torr_info = torr_handle.get_torrent_info()
        peer_req = torr_info.map_file(file_index, 0, 1048576)  # 1048576 (1MB) is a dummy value to avoid C int overflow
        # Start piece of the file
        start_piece = peer_req.piece
        # The number of pieces in the file
        piece_length = torr_info.piece_length()
        num_pieces = int(ceil(files[file_index][1] / piece_length))
        end_piece = min(start_piece + num_pieces, torr_info.num_pieces() - 1)
        self.set_piece_priorities(info_hash, 0)
        if torr_handle.status().paused:
            torr_handle.resume()
        addon.log('Reading the 1st piece...')
        torr_handle.piece_priority(start_piece, 7)
        while not (self._abort_buffering.is_set() or kodi_monitor.abortRequested()):
            xbmc.sleep(200)
            if torr_handle.have_piece(start_piece):
                break
        else:
            return
        addon.log('Trying to determine the video duration...')
        buffer_length, end_offset = self.calculate_buffers(os.path.join(addon.download_dir, files[file_index][0]),
                                                           buffer_duration,
                                                           default_buffer_size,
                                                           num_pieces, piece_length)
        addon.log('buffer_length={0}, end_offset={1}'.format(buffer_length, end_offset))
        addon.log('start_piece={0}, end_piece={1}, piece_length={2}'.format(start_piece,
                                                                            end_piece,
                                                                            piece_length))
        self._streamed_file_data.contents = {'torr_handle': torr_handle,
                                             'buffer_length': buffer_length,
                                             'start_piece': start_piece,
                                             'end_offset': end_offset,
                                             'end_piece': end_piece,
                                             'piece_length': piece_length}
        # Check if the file has been downloaded earlier
        if not self.check_piece_range(torr_handle, start_piece + 1, end_piece):
            # Setup buffer download
            end_pool = range(end_piece - end_offset, end_piece + 1)
            buffer_pool = range(start_piece, start_piece + buffer_length) + end_pool
            buffer_pool_length = len(buffer_pool)
            [torr_handle.piece_priority(piece, 7) for piece in end_pool]
            # torr_handle.set_sequential_download(True)
            self.start_sliding_window_async(torr_handle,
                                            start_piece + 1,
                                            start_piece + sliding_window_length,
                                            end_piece - end_offset - 1)
            while len(buffer_pool) > 0 and not self._abort_buffering.is_set() and not kodi_monitor.abortRequested():
                addon.log('Buffer pool: {0}'.format(str(buffer_pool)))
                xbmc.sleep(200)
                for index, piece_ in enumerate(buffer_pool):
                    if torr_handle.have_piece(piece_):
                        del buffer_pool[index]
                self._buffer_percent.contents = int(100.0 * (buffer_pool_length - len(buffer_pool)) /
                                                    buffer_pool_length)
            if not self._abort_buffering.is_set():
                torr_handle.flush_cache()
        self._buffering_complete.set()

    def start_sliding_window_async(self, torr_handle, window_start, window_end, last_piece):
        """
        Start a sliding window in a separate thread
        """
        self._abort_sliding.set()
        try:
            self._sliding_window_thread.join()
        except (RuntimeError, AttributeError):
            pass
        self._sliding_window_thread = threading.Thread(target=self._sliding_window,
                                                       args=(torr_handle, window_start, window_end, last_piece))
        self._sliding_window_thread.daemon = True
        self._sliding_window_thread.start()

    def _sliding_window(self, torr_handle, window_start, window_end, last_piece):
        """
        Sliding window

        This method implements a sliding window algorithm for sequential download
        of a media file for streaming purposes.
        """
        self._abort_sliding.clear()
        window_end = min(window_end, last_piece)
        [torr_handle.piece_priority(piece, 1) for piece in xrange(window_start, window_end + 1)]
        while window_start <= last_piece and not self._abort_sliding.is_set() and not kodi_monitor.abortRequested():
            addon.log('Sliding window position: {0}'.format(window_start))
            self._sliding_window_position.contents = window_start
            torr_handle.piece_priority(window_start, 7)
            if torr_handle.have_piece(window_start):
                window_start += 1
                if window_end < last_piece:
                    window_end += 1
                    torr_handle.piece_priority(window_end, 1)
            xbmc.sleep(100)
        self._sliding_window_position.contents = -1

    def abort_buffering(self):
        """
        Abort buffering

        :return:
        """
        self._abort_buffering.set()
        self._abort_sliding.set()
        try:
            self._buffer_file_thread.join()
        except (RuntimeError, AttributeError):
            pass
        try:
            self._sliding_window_thread.join()
        except (RuntimeError, AttributeError):
            pass

    def remove_torrent(self, info_hash, delete_files=False):
        """
        Remove torrent

        :param info_hash:
        :param delete_files:
        :return:
        """
        if self.streamed_file_data is not None and info_hash == str(self.streamed_file_data['torr_handle'].info_hash()):
            self.abort_buffering()
        super(Streamer, self).remove_torrent(info_hash, delete_files)

    @staticmethod
    def calculate_buffers(filename, buffer_duration, default_buffer_size, num_pieces, piece_length):
        """
        Calculate buffer length in pieces for provided duration

        :param filename:
        :param buffer_duration:
        :param num_pieces:
        :param piece_length:
        :return:
        """
        try:
            duration = get_duration(filename)
        except HachoirError:
            addon.log('Unable to determine video duration.')
            # Fallback if hachoir cannot parse the file
            end_offset = int(round(4500000 / piece_length, 0))
            buffer_length = int(ceil(1048576 * default_buffer_size / piece_length)) - end_offset
        else:
            addon.log('Video duration: {0}s'.format(duration))
            buffer_length = int(ceil(buffer_duration * num_pieces / duration))
            # For AVI files Kodi requests bigger chunks at the end of a file
            end_offset = int(round(5750000 / piece_length, 0)) if os.path.splitext(filename)[1].lower() == '.avi' else 1
        return buffer_length, end_offset

    @staticmethod
    def check_piece_range(torr_handle, start_piece, end_piece):
        """
        Check if the range of pieces is downloaded

        :param torr_handle:
        :param start_piece:
        :param end_piece:
        :return:
        """
        for piece in xrange(start_piece, end_piece + 1):
            if not torr_handle.have_piece(piece):
                return False
        return True

    @property
    def is_buffering_complete(self):
        """Buffering complete flag"""
        return self._buffering_complete.is_set()

    @property
    def sliding_window_position(self):
        """Sliding window position"""
        return self._sliding_window_position.contents

    @property
    def buffer_percent(self):
        """Buffer %"""
        return self._buffer_percent.contents

    @property
    def streamed_file_data(self):
        """
        Streamed file data

        :return: dict
        """
        return self._streamed_file_data.contents
