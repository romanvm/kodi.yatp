# -*- coding: utf-8 -*-
# Module: streamer
# Author: Roman V.M.
# Created on: 12.05.2015
# License: GPL v.3 https://www.gnu.org/copyleft/gpl.html

import os
from urlparse import urljoin
from time import sleep
from requests import post
import xbmcgui
from addon import Addon


__addon__ = Addon()
json_url = urljoin(__addon__.torrenter_host, 'json-rpc')
media_url = urljoin(__addon__.torrenter_host, 'media')


def _request(data):
    """
    Send JSON-RPC request

    :param data:
    :return:
    """
    return post(json_url, json=data).json()


def get_path(torrent):
    """
    Resolve a playable path from torrent

    :param torrent: str - magnet link or .torrent file URL
    :return:
    """
    _request({'method': 'add_torrent', 'params': [torrent]})
    progress = xbmcgui.DialogProgress()
    progress.create('Buffering torrent', 'Adding torrent...', 'This may take some time.')
    while not (progress.iscanceled() or _request({'method': 'check_torrent_added', 'params': None})['result']):
        sleep(1.0)
    if not progress.iscanceled():
        torrent_data = _request({'method': 'get_data_buffer', 'params': None})['result']
        # Create a list of videofiles in a torrent.
        # Each element is a tuple (<file name>, <file index in a torrent>).
        videofiles = []
        for file_index, file_ in enumerate(torrent_data['files']):
            if os.path.splitext(file_.lower())[1] in ('.avi', '.mkv', '.mp4', '.ts', '.m2ts', '.mov'):
                videofiles.append((file_index, os.path.basename(file_)))
        if videofiles:
            if len(videofiles) > 1:
                index = xbmcgui.Dialog().select('Select a videofile to play', [item[0] for item in videofiles])
            else:
                index = 0
            if index >= 0:
                # Select a vileofile to play
                videofile = videofiles[index]
                _request({'method': 'stream_torrent', 'params': [torrent_data['info_hash'],
                                                                 videofile[0],
                                                                 __addon__.buffer_size]})
                while not (progress.iscanceled() or
                               _request({'method': 'check_buffering_complete', 'params': None})['result']):
                    buffer_progress = _request({'method': 'get_data_buffer', 'params': None})
                    torrent_info = _request({'method': 'get_torrent_info', 'params': [torrent_data['info_hash']]})
                    progress.update(buffer_progress,
                                    'Downloaded: {0}MB'.format(torrent_info['total_download']),
                                    'Download speed: {0}KB/s'.format(torrent_info['dl_speed']),
                                    'Seeds: {0}'.format(torrent_info['num_seeds']))
                    sleep(1.0)
                progress.close()
                if not progress.iscanceled():
                    if len(videofiles) > 1:
                        video_path = urljoin(media_url, torrent_data['name'], videofile[0])
                    else:
                        video_path = urljoin(media_url, videofile[0])
                    return video_path
                else:
                    _request({'method': 'abort_buffering', 'params': None})
                    sleep(0.5)
                    _request({'method': 'remove_torrent', 'params': [torrent_data['info_hash'], True]})
            else:
                xbmcgui.Dialog().notification(__addon__.id, 'A video is not selected', __addon__.icon, 3000)
        else:
            xbmcgui.Dialog().notification(__addon__.id, 'No videofiles to play.', 'error', 3000)
    if not (_request({'method': 'check_torrent_added', 'params': None})['result']
            and _request({'method': 'check_buffering_complete', 'params': None})['result']):
        xbmcgui.Dialog().notification(__addon__.id, 'Playback cancelled.', __addon__.icon, 3000)
    progress.close()
    return None
