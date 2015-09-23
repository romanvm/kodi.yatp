#!usr/bin/env python2
# -*- coding: utf-8 -*-
# Name:        torrenter
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  13.12.2014
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Torrent client

The module implements a simple torrent client based on python-libtorrent library
and with torrent media streaming capability.
"""

from __future__ import division
import os
import sys
import time
import threading
import datetime
import platform
import cPickle as pickle
from math import ceil
from requests import get
import xbmc
from addon import Addon
from utilities import get_duration

addon = Addon()
addon.log('Platform: "{0}"; machine: "{1}"; processor: "{2}"; system: "{3}"'.format(
            sys.platform,
            platform.machine(),
            platform.processor(),
            platform.system()), xbmc.LOGNOTICE)  # This is for potential statistic and debugging purposes

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
        self._lock = threading.Lock()
        self._contents = contents

    @property
    def contents(self):
        with self._lock:
            return self._contents

    @contents.setter
    def contents(self, value):
        with self._lock:
            self._contents = value


class Torrenter(object):
    """
    Torrenter class

    Implements a simple torrent client.
    """
    def __init__(self, start_port=6881, end_port=6891, persistent=False, resume_dir=''):
        """
        Class constructor

        If persistent=False, Torrenter does not store any persistend data
        for torrents.
        @param start_port: int
        @param end_port: int
        @param dl_speed_limit: int - download speed limit in KB/s
        @param ul_speed_limit: int - uplpad speed lomit in KB/s
        @param persistent: bool - store persistent data
        @param resume_dir: str - the dir where session and torrents persistent data are stored.
        @return:
        """
        # torrents_pool is used to map torrent handles to their sha1 hexdigests
        # Item format {hexdigest: torr_handle}
        self._torrents_pool = {}
        # Use persistent storage for session and torrents info
        self._persistent = persistent
        # The directory where session and torrent data are stored
        self._resume_dir = os.path.abspath(resume_dir)
        # Worker threads
        self._add_torrent_thread = None
        # Signal events
        self._torrent_added = threading.Event()
        # Inter-thread data buffer.
        self._last_added_torrent = Buffer()
        # Initialize session
        self._session = libtorrent.session()
        self._session.listen_on(start_port, end_port)
        if self._persistent:
            try:
                self._load_session_state()
            except TorrenterError:
                self._save_session_state()
        self.set_session_settings(cache_size=256,  # 4MB
                                  ignore_limits_on_local_network=False,
                                  user_agent='uTorrent/2200(24683)')
        self._session.add_dht_router('router.bittorrent.com', 6881)
        self._session.add_dht_router('router.utorrent.com', 6881)
        self._session.add_dht_router('router.bitcomet.com', 6881)
        self._session.start_dht()
        if self._persistent:
            self._load_torrents()

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
        if self._persistent:
            self.save_all_resume_data()
        del self._session

    def set_encryption_policy(self, enc_policy=1):
        """
        Set encryption policy for the session

        @param enc_policy: int - 0 = forced, 1 = enabled, 2 = disabled
        @return:
        """
        pe_settings = self._session.get_pe_settings()
        pe_settings.in_enc_policy = pe_settings.out_enc_policy = libtorrent.enc_policy(enc_policy)
        self._session.set_pe_settings(pe_settings)

    def set_session_settings(self, **settings):
        """
        Set session settings.

        See U{libtorrent API docs<http://www.rasterbar.com/products/libtorrent/manual.html#session-customization>}
        for more info.
        @param settings: session settings key=value pairs
        @return:
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
        @param torrent: str - path to a .torrent file or a magnet link
        @param save_path: str - save path
        @param zero_priorities: bool
        @return:
        """
        self._add_torrent_thread = threading.Thread(target=self.add_torrent,
                                                    args=(torrent, save_path, paused, cookies))
        self._add_torrent_thread.daemon = True
        self._add_torrent_thread.start()

    def add_torrent(self, torrent, save_path, paused=False, cookies=None):
        """
        Add a torrent download

        @param torrent: str
        @param save_path: str
        @param zero_priorities: bool
        @return: dict {'name': str, 'info_hash': str, 'files': list}
        """
        self._torrent_added.clear()
        torr_handle = self._add_torrent(torrent, save_path, paused=paused, cookies=cookies)
        if self._persistent:
            self._save_torrent_info(torr_handle)
        info_hash = str(torr_handle.info_hash())
        result = {'name': torr_handle.name().decode('utf-8'), 'info_hash': info_hash}
        torr_info = torr_handle.get_torrent_info()
        result['files'] = [[file_.path.decode('utf-8'), file_.size] for file_ in torr_info.files()]
        self._last_added_torrent.contents = result
        self._torrent_added.set()

    def _add_torrent(self, torrent, save_path, resume_data=None, paused=False, cookies=None):
        """
        Add a torrent to the pool.

        @param torrent: str - the path to a .torrent file or a magnet link
        @param save_path: str - torrent save path
        @param resume_data: str - bencoded torrent resume data
        @return: object - torr_handle
        """
        add_torrent_params = {'save_path': os.path.abspath(save_path),
                              'storage_mode': libtorrent.storage_mode_t.storage_mode_sparse,
                              'paused': paused}
        if resume_data is not None:
            add_torrent_params['resume_data'] = resume_data
        if isinstance(torrent, dict):
            add_torrent_params['ti'] = libtorrent.torrent_info(torrent)
        elif torrent[:7] == 'magnet:':
            add_torrent_params['url'] = str(torrent)  # libtorrent doesn't like unicode objects here
        elif torrent[:7] in ('http://', 'https:/'):
            # Here external http/https client is used in case if libtorrent module is compiled without OpenSSL
            add_torrent_params['ti'] = libtorrent.torrent_info(libtorrent.bdecode(self.load_torrent(torrent, cookies)))
        else:
            try:
                add_torrent_params['ti'] = libtorrent.torrent_info(os.path.abspath(torrent))
            except RuntimeError:
                raise TorrenterError('Invalid path to the .torrent file!')
        torr_handle = self._session.add_torrent(add_torrent_params)
        while not torr_handle.has_metadata():  # Wait until torrent metadata are populated
            time.sleep(0.1)
        torr_handle.auto_managed(False)
        self._torrents_pool[str(torr_handle.info_hash())] = torr_handle
        return torr_handle

    def _get_torrent_status(self, info_hash):
        """
        Get torrent status

        @param info_hash: str
        @return: object status
        """
        try:
            torr_handle = self._torrents_pool[info_hash]
        except KeyError:
            raise TorrenterError('Invalid torrent hash!')
        if torr_handle.is_valid():
            torr_status = torr_handle.status()
        else:
            torr_status = None
        return torr_status

    def _get_torrent_info(self, info_hash):
        """
        Get torrent info

        @param info_hash: str
        @return: object torrent_info
        """
        try:
            torr_info = self._torrents_pool[info_hash].get_torrent_info()
        except KeyError:
            raise TorrenterError('Invalid torrent hash!')
        return torr_info

    def remove_torrent(self, info_hash, delete_files=False):
        """
        Remove a torrent from download

        @param info_hash: str
        @return:
        """
        try:
            self._session.remove_torrent(self._torrents_pool[info_hash], delete_files)
            del self._torrents_pool[info_hash]
            if self._persistent:
                os.remove(os.path.join(self._resume_dir, info_hash + '.resume'))
                os.remove(os.path.join(self._resume_dir, info_hash + '.torrent'))
        except (KeyError, OSError):
            raise TorrenterError('Invalid torrent hash or info files not found!')

    def _save_session_state(self):
        """
        Save session state

        @return:
        """
        if self._persistent:
            with open(os.path.join(self._resume_dir, 'session.state'), mode='wb') as state_file:
                pickle.dump(self._session.save_state(), state_file)
        else:
            raise TorrenterError('Trying to save the state of a non-persistent instance!')

    def _load_session_state(self):
        """
        Load session state

        @return:
        """
        try:
            with open(os.path.join(self._resume_dir, 'session.state'), mode='rb') as state_file:
                self._session.load_state(pickle.load(state_file))
        except IOError:
            raise TorrenterError('.state file not found!')

    def pause_torrent(self, info_hash, graceful_pause=1):
        """
        Pause a torrent
        @param info_hash: str
        @return:
        """
        try:
            self._torrents_pool[info_hash].pause(graceful_pause)
        except KeyError:
            raise TorrenterError('Invalid torrent hash!')

    def resume_torrent(self, info_hash):
        """
        Resume a torrent

        @param info_hash: str
        @return:
        """
        try:
            self._torrents_pool[info_hash].resume()
        except KeyError:
            raise TorrenterError('Invalid torrent hash!')

    def _save_resume_data(self, info_hash, force_save=False):
        """
        Save fast-resume data for a torrent.

        @param info_hash: str
        @return:
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

        @return:
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

        @param torr_handle: object - torrent handle
        @return:
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

        @param filepath: str
        @return:
        """
        with open(filepath, mode='rb') as m_file:
            metadata = pickle.load(m_file)
        torrent = os.path.join(self._resume_dir, metadata['info_hash'] + '.torrent')
        self._add_torrent(torrent, metadata['save_path'], metadata['resume_data'])

    def _load_torrents(self):
        """
        Load all torrents

        @return:
        """
        dir_listing = os.listdir(self._resume_dir)
        for item in dir_listing:
            if item[-7:] == '.resume':
                self._load_torrent_info(os.path.join(self._resume_dir, item))

    def get_torrent_info(self, info_hash):
        """
        Get torrent info in a human-readable format

        The following info is returned:
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
        @param info_hash: str
        @return: dict - torrent info
        """
        torr_info = self._get_torrent_info(info_hash)
        torr_status = self._get_torrent_status(info_hash)
        completed_time = str(datetime.datetime.fromtimestamp(int(torr_status.completed_time)))
        return {'name': torr_info.name().decode('utf-8'),
                'size': int(torr_info.total_size() / 1048576),
                'state': str(torr_status.state) if not torr_status.paused else 'paused',
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
        @return: list - the list of torrent info dicts
        """
        listing = []
        for info_hash in self._torrents_pool.iterkeys():
            listing.append(self.get_torrent_info(info_hash))
        return listing

    def pause_all(self, graceful_pause=1):
        """
        Pause all torrents

        @return:
        """
        for info_hash in self._torrents_pool.iterkeys():
            self.pause_torrent(info_hash, graceful_pause)

    def resume_all(self):
        """
        Resume all torrents

        @return:
        """
        for info_hash in self._torrents_pool.iterkeys():
            self.resume_torrent(info_hash)

    def prioritize_file(self, info_hash, file_index, priority):
        """
        Prioritize a file in a torrent

        If all piece priorities in the torrent are set to 0, to enable downloading an individual file
        priority value must be no less than 2.
        @param info_hash: str - torrent info-hash
        @param file_index: int - the index of a file in the torrent
        @param priority: int - priority from 0 to 7.
        @return:
        """
        self._torrents_pool[info_hash].file_priority(file_index, priority)

    def set_piece_priorities(self, info_hash, priority=1):
        """
        Set priorities for all pieces in a torrent

        @param info_hash: str
        @param priority: int
        @return:
        """
        torr_handle = self._torrents_pool[info_hash]
        [torr_handle.piece_priority(piece, priority) for piece in xrange(torr_handle.get_torrent_info().num_pieces())]

    @staticmethod
    def load_torrent(url, cookies=None):
        """Load .torrent from URL"""
        return get(url, cookies=cookies).content

    @property
    def is_torrent_added(self):
        """Torrent added flag"""
        return self._torrent_added.is_set()

    @property
    def last_added_torrent(self):
        """The last added torrent info"""
        return self._last_added_torrent.contents


class Streamer(Torrenter):
    """
    Torrent Streamer class

    Implements a torrent client with media streaming capability
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

    def buffer_file_async(self, file_index, buffer_duration, sliding_window_length, default_buffer_size):
        """
        Force sequential download of file for video playback.

        This method will stream a torrent in a separate thread. The caller should periodically
        check buffering_complete flag. If buffering needs to be terminated,
        the caller should call abort_buffering method.
        The torrent must be already added via add_torrent method!
        @param file_index: int - the numerical index of the file to be streamed.
        @param buffer_duration: int - buffer duration in s
        @param sliding_window_length: int - the length of a sliding window in pieces
        @param default_buffer_size: int - fallback buffer size if a video cannot be parsed by hachoir
        @return:
        """
        self._buffer_file_thread = threading.Thread(target=self._buffer_file, args=(file_index,
                                                                                    buffer_duration,
                                                                                    sliding_window_length,
                                                                                    default_buffer_size))
        self._buffer_file_thread.daemon = True
        self._buffer_file_thread.start()

    def _buffer_file(self, file_index, buffer_duration, sliding_window_length, default_buffer_size):
        """
        Force sequential download of file for video playback.

        The torrent must be already added via add_torrent method!
        @param file_index: int - the numerical index of the file to be streamed.
        @param buffer_duration: int - buffer duration in s
        @param sliding_window_length: int - the length of a sliding window in pieces
        @param default_buffer_size: int - fallback buffer size if a video cannot be parsed by hachoir
        @return:
        """
        if file_index >= len(self.last_added_torrent['files']) or file_index < 0:
            raise IndexError('Invalid file index: {0}!'.format(file_index))
        # Clear flags
        self._buffering_complete.clear()
        self._abort_buffering.clear()
        self._buffer_percent.contents= 0
        torr_handle = self._torrents_pool[self.last_added_torrent['info_hash']]
        torr_info = torr_handle.get_torrent_info()
        # Pick the file to be streamed from the torrent files
        file_entry = torr_info.files()[file_index]
        peer_req = torr_info.map_file(file_index, 0, 1048576)  # 1048576 (1MB) is a dummy value to avoid C int overflow
        # Start piece of the file
        start_piece = peer_req.piece
        # The number of pieces in the file
        piece_length = torr_info.piece_length()
        num_pieces = int(ceil(file_entry.size / piece_length))
        end_piece = min(start_piece + num_pieces, torr_info.num_pieces() - 1)
        self.set_piece_priorities(self.last_added_torrent['info_hash'], 0)
        if torr_handle.status().paused:
            torr_handle.resume()
        torr_handle.piece_priority(start_piece, 7)
        while not torr_handle.have_piece(start_piece):
            time.sleep(0.2)
        buffer_length, end_offset = self.calculate_buffers(os.path.join(addon.download_dir,
                                                                    self.last_added_torrent['files'][file_index][0]),
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
            while len(buffer_pool) > 0 and not self._abort_buffering.is_set():
                addon.log('Buffer pool: {0}'.format(str(buffer_pool)))
                time.sleep(0.2)
                for index, piece_ in enumerate(buffer_pool):
                    if torr_handle.have_piece(piece_):
                        del buffer_pool[index]
                self._buffer_percent.contents = int(100.0 * (buffer_pool_length - len(buffer_pool)) /
                                                    buffer_pool_length)
            if not self._abort_buffering.is_set():
                torr_handle.flush_cache()
                self._buffering_complete.set()
        else:
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
        while window_start <= last_piece and not self._abort_sliding.is_set():
            addon.log('Sliding window position: {0}'.format(window_start))
            self._sliding_window_position.contents = window_start
            torr_handle.piece_priority(window_start, 7)
            if torr_handle.have_piece(window_start):
                window_start += 1
                if window_end < last_piece:
                    window_end += 1
                    torr_handle.piece_priority(window_end, 1)
            time.sleep(0.1)
        self._sliding_window_position.contents = -1

    def abort_buffering(self):
        """
        Abort buffering

        @return:
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

        @param info_hash:
        @param delete_files:
        @return:
        """
        if self.streamed_file_data is not None and info_hash == str(self.streamed_file_data['torr_handle'].info_hash()):
            self.abort_buffering()
        super(Streamer, self).remove_torrent(info_hash, delete_files)

    @staticmethod
    def calculate_buffers(filename, buffer_duration, default_buffer_size, num_pieces, piece_length):
        """
        Calculate buffer length in pieces for provided duration

        @param filename:
        @param buffer_duration:
        @param num_pieces:
        @param piece_length:
        @return:
        """
        duration = get_duration(filename)
        addon.log('Video duration: {0}s'.format(duration))
        if duration:
            buffer_length = int(ceil(buffer_duration * num_pieces / duration))
            # For AVI files Kodi requests bigger chunks at the end of a file
            end_offset = int(round(4194304 / piece_length, 0)) if os.path.splitext(filename)[1].lower() == '.avi' else 1
        else:
            # Fallback if hachoir cannot parse the file
            end_offset = int(round(4194304 / piece_length, 0))
            buffer_length = int(ceil(1048576 * default_buffer_size / piece_length)) - end_offset
        return buffer_length, end_offset

    @staticmethod
    def check_piece_range(torr_handle, start_piece, end_piece):
        """
        Check if the range of pieces is downloaded

        @param torr_handle:
        @param start_piece:
        @param end_piece:
        @return:
        """
        result = True
        for piece in xrange(start_piece, end_piece + 1):
            if not torr_handle.have_piece(piece):
                result = False
                break
        return result

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

        @return: dict
        """
        return self._streamed_file_data.contents


def serve_file_from_torrent(file_, byte_position, torrent_handle, start_piece, piece_length, oncreen_label):
    """
    Serve a file from torrent by pieces

    This iterator function serves a video file being downloaded to Kodi piece by piece.
    If some piece is not downloaded, the function prioritizes it
    and then waits until it is downloaded.
    @param byte_position: the start byte
    @param torrent_handle: streamed torrent's handle
    @param start_piece: file's start piece
    @param piece_length: piece length in bytes
    @param oncreen_label: on_screen_label instance to show waiting status
    """
    paused = False  # Needed to prevent unpausing video paused by a user.
    with file_:
        while True:
            current_piece = start_piece + int(byte_position / piece_length)
            addon.log('Checking piece #{0}'.format(current_piece))
            # Wait for the piece if it is not downloaded
            while not torrent_handle.have_piece(current_piece):
                if torrent_handle.piece_priority(current_piece) < 7:
                    torrent_handle.piece_priority(current_piece, 7)
                if not xbmc.getCondVisibility('Player.Paused'):
                    xbmc.executebuiltin('Action(Pause)')
                    paused = True
                    addon.log('Paused to wait for piece #{0}.'.format(current_piece))
                if paused:
                    oncreen_label.text = addon.get_localized_string(32050).format(
                        current_piece,
                        int(torrent_handle.status().download_payload_rate / 1024))
                    oncreen_label.show()
                addon.log('Waiting for piece #{0}...'.format(current_piece))
                xbmc.sleep(1000)  # xbmc.sleep works better here
            if paused:
                xbmc.executebuiltin('Action(Play)')
                paused = False
                addon.log('Piece #{0} downloaded. Continue playback.'.format(current_piece))
                oncreen_label.hide()
            file_.seek(byte_position)
            chunk = file_.read(piece_length)
            if not chunk:
                break
            addon.log('Serving piece #{0}'.format(current_piece))
            yield chunk
            byte_position += piece_length
