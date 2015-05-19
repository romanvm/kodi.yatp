# -*- coding: utf-8 -*-
# Module: streamer
# Author: Roman V.M.
# Created on: 12.05.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
import re
import time
import threading
import xbmcgui
import xbmcvfs
#
from torrenter import Torrenter, TorrenterError


class Streamer(object):
    """Streamer Class"""
    def __init__(self, download_dir, keep_files=False):
        """Class constructor"""
        self._torrenter = Torrenter(30000, 30010)
        self.download_dir = download_dir
        self.delete_files = not keep_files
        if not xbmcvfs.exists(self.download_dir):
            xbmcvfs.mkdir(self.download_dir)
        self._add_torrent_thread = None
        self._stream_thread = None
        self._file_size = 0

    def __del__(self):
        """Class destructor"""
        self._torrenter.abort_streaming()
        try:
            self._stream_thread.join()
        except (RuntimeError, AttributeError):
            pass
        try:
            self._torrenter.remove_torrent(self.delete_files)
        except TorrenterError:
            pass
        del self._torrenter

    def stream(self, torrent_path, buffer_percent=3.0):
        """
        Download a video torrent in a sequential way.
        :param torrent_path: str - a path to a .torrent file or a magnet link.
        :param buffer_percent: float - buffer size in %
        :return: str - a path to the videofile
        """
        dialog_progress = xbmcgui.DialogProgress()
        dialog_progress.create('Buffering torrent')
        dialog_progress.update(0, 'Adding torrent...',
                               'This may take some time.',
                               'Please wait until download starts.')
        self._add_torrent_thread = threading.Thread(target=self._torrenter.add_torrent_async,
                                                    args=(torrent_path, self.download_dir, True))
        self._add_torrent_thread.daemon = True
        self._add_torrent_thread.start()
        # Adding a magnet link may take a while
        while not self._torrenter.torrent_added and not dialog_progress.iscanceled():
            time.sleep(0.5)
        if not dialog_progress.iscanceled():
            # Create a list of videofiles in a torrent.
            # Each element is a tuple (<file name>, <file index in a torrent>).
            videofiles = []
            for file_index in xrange(len(self._torrenter.files)):
                if re.search(r'\.(mp4|avi|mkv|m4v|mov|wmv|ts)', self._torrenter.files[file_index].lower()) is not None:
                    videofiles.append((os.path.basename(self._torrenter.files[file_index]), file_index))
            if videofiles:
                if len(videofiles) > 1:
                    index = xbmcgui.Dialog().select('Select a videofile to play', [item[0] for item in videofiles])
                else:
                    index = 0
                if index >= 0:
                    # Select a vileofile to play
                    videofile = videofiles[index]
                    torr_info = self._torrenter.torrent.get_torrent_info()
                    self._file_size = int(torr_info.files()[videofile[1]].size)
                    self._stream_thread = threading.Thread(target=self._torrenter.stream_torrent_async,
                                                           args=(videofile[1], buffer_percent))
                    self._stream_thread.daemon = True
                    self._stream_thread.start()
                    while not self._torrenter.buffering_complete and not dialog_progress.iscanceled():
                        dialog_progress.update(int(10000 * self._get_torrent_status().total_done /
                                                   (self._file_size * buffer_percent)),
                                               'Downloaded: {0}MB'.format(self.total_download),
                                               'Download speed: {0}KB/s'.format(self.dl_speed),
                                               'Peers: {0}'.format(self.num_peers))
                        time.sleep(1.0)
                    dialog_progress.close()
                    if not dialog_progress.iscanceled():
                        if len(self._torrenter.files) > 1:
                            video_path = os.path.join(self.download_dir, self._torrenter.torrent.name(), videofile[0])
                        else:
                            video_path = os.path.join(self.download_dir, videofile[0])
                        return video_path
                else:
                    xbmcgui.Dialog().notification('Note!', 'A video is not selected', 'info', 3000)
            else:
                xbmcgui.Dialog().notification('Error!', 'No videofiles to play.', 'error', 3000)
        if dialog_progress.iscanceled():
            self._torrenter.abort_streaming()
            try:
                self._stream_thread.join()
            except (RuntimeError, AttributeError):
                pass
            xbmcgui.Dialog().notification('Note!', 'Playback cancelled.', 'info', 3000)
        return None

    def _get_torrent_status(self):
        """
        Get torrent status object
        :return:
        """
        try:
            return self._torrenter.torrent.status()
        except AttributeError:
            return None

    @property
    def total_download(self):
        """
        Total download in MB
        :return: int
        """
        status = self._get_torrent_status()
        if status is not None:
            # total_done property holds correct volume of useful downloaded data.
            # total_payload_download returns incorrect value (with some overhead?)
            return int(status.total_done) / 1048576
        else:
            return 0

    @property
    def total_upload(self):
        """
        Total upload in MB
        :return: int
        """
        status = self._get_torrent_status()
        if status is not None:
            return int(status.total_payload_upload) / 1048576
        else:
            return 0

    @property
    def dl_speed(self):
        """
        DL speed in KB/s
        :return: int
        """
        status = self._get_torrent_status()
        if status is not None:
            return status.download_payload_rate / 1024
        else:
            return 0

    @property
    def ul_speed(self):
        """
        UL speed in KB/s
        :return: int
        """
        status = self._get_torrent_status()
        if status is not None:
            return status.upload_payload_rate / 1024
        else:
            return 0

    @property
    def num_peers(self):
        """
        The number of peers
        :return: int
        """
        status = self._get_torrent_status()
        if status is not None:
            return status.num_peers
        else:
            return 0

    @property
    def is_seeding(self):
        """
        Seeding status as bool
        :return: bool
        """
        status = self._get_torrent_status()
        if status is not None:
            return status.is_seeding
        else:
            return False

    @property
    def file_size(self):
        """
        The size of a file being streamed in MB
        :return: int
        """
        return self._file_size / 1048576

    @property
    def progress(self):
        """
        Download progress in %
        :return: int
        """
        return 100 * self.total_download / self.file_size
