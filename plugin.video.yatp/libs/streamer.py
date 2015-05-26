# -*- coding: utf-8 -*-
# Module: streamer
# Author: Roman V.M.
# Created on: 12.05.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import time
import threading
import xbmcgui
import xbmcvfs
#
from torrenter import Torrenter, TorrenterError


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

    def stream(self, torrent_path, buffer_percent=3.0, streaming=True):
        """
        Download a video torrent in a sequential way.
        :param torrent_path: str - a path to a .torrent file or a magnet link.
        :param buffer_percent: float - buffer size in %
        :return: str - a path to the videofile
        """
        result = False
        dialog_progress = xbmcgui.DialogProgress()
        dialog_progress.create('Adding torrent...')
        dialog_progress.update(0, 'This may take some time.', 'Please wait until download starts.')
        self._add_torrent_thread = threading.Thread(target=self.add_torrent_async,
                                                    args=(torrent_path, self._download_dir, True))
        self._add_torrent_thread.daemon = True
        self._add_torrent_thread.start()
        # Adding a magnet link may take a while
        while not self.torrent_added and not dialog_progress.iscanceled():
            time.sleep(0.5)
        if not dialog_progress.iscanceled():
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
                    if streaming:
                        result = self.pre_buffer_stream(buffer_percent)
                    else:
                        result = self.buffer_file(buffer_percent)
                    if result:
                        if len(self.files) > 1:
                            video_path = os.path.join(self._download_dir, self.torrent.name(), videofile[0])
                        else:
                            video_path = os.path.join(self._download_dir, videofile[0])
                        return video_path
                else:
                    xbmcgui.Dialog().notification('Note!', 'A video is not selected', 'info', 3000)
            else:
                xbmcgui.Dialog().notification('Error!', 'No videofiles to play.', 'error', 3000)
        if dialog_progress.iscanceled() or not result:
            self.abort_streaming()
            try:
                self._buffer_thread.join()
            except (RuntimeError, AttributeError):
                pass
            xbmcgui.Dialog().notification('Note!', 'Playback cancelled.', 'info', 3000)
        return None

    def pre_buffer_stream(self, buffer_percent):
        """
        Pre-buffer videofile
        :return:
        """
        dialog_progress = xbmcgui.DialogProgress()
        dialog_progress.create('Buffering torrent...')
        self._buffer_thread = threading.Thread(target=self.stream_torrent_async, args=(self.file_index, buffer_percent))
        self._buffer_thread.daemon = True
        self._buffer_thread.start()
        while not self.buffering_complete and not dialog_progress.iscanceled():
            dialog_progress.update(int(10000 * self.torrent_status.total_done /
                                       (self._file_size * buffer_percent)),
                                   'Downloaded: {0}MB'.format(self.total_download),
                                   'Download speed: {0}KB/s'.format(self.dl_speed),
                                   'Peers: {0}'.format(self.num_peers))
            time.sleep(1.0)
        dialog_progress.close()
        return not dialog_progress.iscanceled()

    def buffer_file(self, buffer_percent, offset=0):
        """
        Buffer video file
        :param buffer_percent: int
        :param offset: int
        :return:
        """
        dialog_progress = xbmcgui.DialogProgress()
        dialog_progress.create('Buffering torrent...')
        self._buffer_thread = threading.Thread(target=self.bufer_torrent_async,
                                               args=(self.file_index, buffer_percent, offset))
        self._buffer_thread.daemon = True
        self._buffer_thread.start()
        while not self.buffering_complete and not dialog_progress.iscanceled():
            dialog_progress.update(self.data_buffer,
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
        Internal index of the fideofile being streamed
        :return:
        """
        return self._file_index

    @property
    def progress(self):
        """
        Download progress in %
        :return: int
        """
        return 100 * self.total_download / self.file_size

    @property
    def pieces_info(self):
        """
        Pieces info for the file being streamed
        :return:
        """
        return self.get_pieces_info(self.file_index)
