# -*- coding: utf-8 -*-
# Module: streamer
# Author: Roman V.M.
# Created on: 12.05.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import sys
import time
import threading
import xbmcgui
import xbmcvfs
import xbmc
#
from torrenter import Torrenter, TorrenterError
from addon import Addon

__addon__ = Addon()


class Streamer(Torrenter):
    """Streamer Class"""
    def __init__(self, download_dir, keep_files=False):
        """Class constructor"""
        super(Streamer, self).__init__(32000, 32010)
        self._download_dir = download_dir
        self._delete_files = not keep_files
        if not xbmcvfs.exists(self._download_dir):
            xbmcvfs.mkdir(self._download_dir)
        self._add_torrent_thread = None
        self._buffer_thread = None
        self._file_size = 0
        self._file_index = None
        self._secs_per_piece = 0.0

    def __del__(self):
        """Class destructor"""
        self.abort_streaming()
        try:
            self._buffer_thread.join()
        except (RuntimeError, AttributeError):
            pass
        try:
            self.remove_torrent(self._delete_files)
        except TorrenterError:
            pass
        super(Streamer, self).__del__()

    def stream(self, torrent_path, buffer_size=__addon__.buffer_size):
        """
        Download a video torrent in a sequential way.
        :param torrent_path: str - a path to a .torrent file or a magnet link.
        :param buffer_size: int - buffer size in MB
        :return: str - a path to the videofile
        """
        buffering_complete = False
        torent_added = self._add_torrent(torrent_path)
        if torent_added:
            # Create a list of videofiles in a torrent.
            # Each element is a tuple (<file name>, <file index in a torrent>).
            videofiles = []
            for file_index in xrange(len(self.files)):
                if os.path.splitext(self.files[file_index].lower())[1] in ('.avi', '.mkv', '.mp4', '.ts', '.m2ts', '.mov'):
                    videofiles.append((os.path.basename(self.files[file_index]), file_index))
            if videofiles:
                if len(videofiles) > 1:
                    index = xbmcgui.Dialog().select('Select a videofile to play', [item[0] for item in videofiles])
                else:
                    index = 0
                if index >= 0:
                    # Select a vileofile to play
                    videofile = videofiles[index]
                    self._file_index = videofile[1]
                    self._file_size = int(self.torrent_info.files()[self.file_index].size)
                    buffering_complete = self.pre_buffer_stream(buffer_size)
                    if buffering_complete:
                        if len(self.files) > 1:
                            video_path = os.path.join(self._download_dir, self.torrent.name(), videofile[0])
                        else:
                            video_path = os.path.join(self._download_dir, videofile[0])
                        return video_path
                else:
                    xbmcgui.Dialog().notification(__addon__.id, 'A video is not selected', __addon__.icon, 3000)
            else:
                xbmcgui.Dialog().notification(__addon__.id, 'No videofiles to play.', 'error', 3000)
        if not (torent_added and buffering_complete):
            self.abort_streaming()
            try:
                self._buffer_thread.join()
            except (RuntimeError, AttributeError):
                pass
            xbmcgui.Dialog().notification(__addon__.id, 'Playback cancelled.', __addon__.icon, 3000)
        return None

    def download_torrent(self, torrent_path):
        """
        Download a torrent to a specified folder
        :param torrent_path:
        :return:
        """
        if self._add_torrent(torrent_path, False):
            progress_thread = threading.Thread(target=self.download_progress_async, args=(self.torrent.name(),))
            progress_thread.start()

    def download_progress_async(self, torrent_name):
        """
        Download
        :param torrent_name:
        :return:
        """
        self._thread_lock.acquire()
        progressbar = xbmcgui.DialogProgressBG()
        progressbar.create('Downloading torrent: {0}'.format(torrent_name))
        monitor = xbmc.Monitor()
        while not (self.is_seeding or monitor.waitForAbort(1.0)):
            progressbar.update(self.torrent_progress,
                               message='DL: {0}MB, DL progr: {1}%; DL sp: {2}KB/s; Peers: {3}'.format(
                                   self.total_download,
                                   self.torrent_progress,
                                   self.dl_speed,
                                   self.num_peers))
        progressbar.close()
        self._thread_lock.release()
        xbmcgui.Dialog().notification(__addon__.id,
                                      'Torrent {0} downloaded!'.format(torrent_name),
                                      __addon__.icon,
                                      3000)
        del self._session
        sys.exit()

    def _add_torrent(self, torrent_path, zero_priorities=True):
        """
        Add a torrent
        :return:
        """
        dialog_progress = xbmcgui.DialogProgress()
        dialog_progress.create('Adding torrent...')
        dialog_progress.update(0, 'This may take some time.', 'Please wait until download starts.')
        self._add_torrent_thread = threading.Thread(target=self.add_torrent_async,
                                                    args=(torrent_path, self._download_dir, zero_priorities))
        self._add_torrent_thread.daemon = True
        self._add_torrent_thread.start()
        # Adding a magnet link may take a while
        while not self.torrent_added and not dialog_progress.iscanceled():
            time.sleep(0.5)
        dialog_progress.close()
        return not dialog_progress.iscanceled()

    def pre_buffer_stream(self, buffer_size):
        """
        Pre-buffer videofile
        :param buffer_size: int - buffer size in MB
        :return:
        """
        dialog_progress = xbmcgui.DialogProgress()
        dialog_progress.create('Buffering torrent...')
        self._buffer_thread = threading.Thread(target=self.stream_torrent_async, args=(self.file_index, buffer_size))
        self._buffer_thread.daemon = True
        self._buffer_thread.start()
        while not self.buffering_complete and not dialog_progress.iscanceled():
            dialog_progress.update(100 * self.torrent_status.total_done / (buffer_size * 1048576),
                                   'Downloaded: {0}MB'.format(self.total_download),
                                   'Download speed: {0}KB/s'.format(self.dl_speed),
                                   'Peers: {0}'.format(self.num_peers))
            time.sleep(1.0)
        dialog_progress.close()
        return not dialog_progress.iscanceled()

    def set_piece_deadlines(self, curr_time, total_time):
        """
        Set piece deadlines for the videofile being streamed
        :param curr_time: float -
        :param total_time:
        :return:
        """
        self.set_secs_per_piece(total_time)
        curr_piece = self.get_current_piece(curr_time)
        msecs_per_piece_dl = 1000.0 * (total_time - curr_time) / (self.pieces_info[1] - curr_piece)
        [self.torrent.set_piece_deadline(piece, int(msecs_per_piece_dl * (piece - curr_piece)))
         for piece in xrange(curr_piece, self.pieces_info[1])]

    def set_secs_per_piece(self, total_time):
        """
        Set seconds_per_piece parameter
        :param total_time: float
        :return:
        """
        self._secs_per_piece = total_time / self.pieces_info[1]

    def get_current_piece(self, curr_time):
        """
        Get currently played piece
        :param curr_time:
        :return:
        """
        return self.pieces_info[0] + int(curr_time / self._secs_per_piece)

    def check_piece(self, piece):
        """
        Check piece availability
        :param piece:
        :return:
        """
        return self.torrent.has_piece(piece)

    @property
    def file_size(self):
        """
        The size of a file being streamed in MB
        :return: int
        """
        return self._file_size / 1048576

    @property
    def file_index(self):
        """
        Internal index of the videofile being streamed
        :return:
        """
        return self._file_index

    @property
    def file_progress(self):
        """
        Download progress in %
        :return: int
        """
        return 100 * self.total_download / self.file_size

    @property
    def pieces_info(self):
        """
        Pieces info for the file being streamed
        :return: tuple - start piece, # of pieces
        """
        return self.get_pieces_info(self.file_index)
