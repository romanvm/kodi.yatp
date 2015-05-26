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


class Streamer(Torrenter):
    """Streamer Class"""
    def __init__(self, download_dir, keep_files=False):
        """Class constructor"""
        super(Streamer, self).__init__(32000, 32010)
        self.download_dir = download_dir
        self.delete_files = not keep_files
        if not xbmcvfs.exists(self.download_dir):
            xbmcvfs.mkdir(self.download_dir)
        self._add_torrent_thread = None
        self._stream_thread = None
        self._file_size = 0

    def __del__(self):
        """Class destructor"""
        self._abort_streaming.set()
        try:
            self._stream_thread.join()
        except (RuntimeError, AttributeError):
            pass
        try:
            self.remove_torrent(self.delete_files)
        except TorrenterError:
            pass
        super(Streamer, self).__del__()

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
        self._add_torrent_thread = threading.Thread(target=self.add_torrent_async,
                                                    args=(torrent_path, self.download_dir, True))
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
                if re.search(r'\.(mp4|avi|mkv|m4v|mov|wmv|ts)', self.files[file_index].lower()) is not None:
                    videofiles.append((os.path.basename(self.files[file_index]), file_index))
            if videofiles:
                if len(videofiles) > 1:
                    index = xbmcgui.Dialog().select('Select a videofile to play', [item[0] for item in videofiles])
                else:
                    index = 0
                if index >= 0:
                    # Select a vileofile to play
                    videofile = videofiles[index]
                    self._file_size = int(self.torrent_info.files()[videofile[1]].size)
                    self._stream_thread = threading.Thread(target=self.stream_torrent_async,
                                                           args=(videofile[1], buffer_percent))
                    self._stream_thread.daemon = True
                    self._stream_thread.start()
                    while not self.buffering_complete and not dialog_progress.iscanceled():
                        dialog_progress.update(int(10000 * self.torrent_status.total_done /
                                                   (self._file_size * buffer_percent)),
                                               'Downloaded: {0}MB'.format(self.total_download),
                                               'Download speed: {0}KB/s'.format(self.dl_speed),
                                               'Peers: {0}'.format(self.num_peers))
                        time.sleep(1.0)
                    dialog_progress.close()
                    if not dialog_progress.iscanceled():
                        if len(self.files) > 1:
                            video_path = os.path.join(self.download_dir, self.torrent.name(), videofile[0])
                        else:
                            video_path = os.path.join(self.download_dir, videofile[0])
                        return video_path
                else:
                    xbmcgui.Dialog().notification('Note!', 'A video is not selected', 'info', 3000)
            else:
                xbmcgui.Dialog().notification('Error!', 'No videofiles to play.', 'error', 3000)
        if dialog_progress.iscanceled():
            self.abort_streaming()
            try:
                self._stream_thread.join()
            except (RuntimeError, AttributeError):
                pass
            xbmcgui.Dialog().notification('Note!', 'Playback cancelled.', 'info', 3000)
        return None

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
