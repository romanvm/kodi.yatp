# coding: utf-8
# Module: utilities
# Created on: 21.08.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import os
import time
from mimetypes import guess_type
import xbmc
from addon import Addon

MIME = {'.mkv': 'video/x-matroska',
        '.mp4': 'video/mp4',
        '.avi': 'video/avi',
        '.ts': 'video/vnd.dlna.mpeg-tts',
        '.m2ts': 'video/vnd.dlna.mpeg-tts',
        '.mov': 'video/quicktime'}
addon = Addon()


def serve_file_from_torrent(file_, byte_position, torrent_handle, start_piece, num_pieces, piece_length, label):
    """
    Serve a file from torrent by pieces

    This iterator function serves a video file being downloaded to Kodi piece by piece.
    If some piece is not downloaded, the function prioritizes it
    and then waits until it is downloaded.
    """
    paused = False  # Needed to prevent unpausing video paused by a user.
    video_duration = 0
    pieces_per_second = 0
    player = xbmc.Player()
    with file_:
        while True:
            current_piece = start_piece + byte_position / piece_length
            if not video_duration:
                addon.log('Video duration: {0}'.format(player.getTotalTime()))
                video_duration = int(player.getTotalTime())
            else:
                pieces_per_second = float(num_pieces) / video_duration
                addon.log('Pieces per second: {}'.format(pieces_per_second))
            addon.log('Current playtime: {0}'.format(player.getTime()))
            # Wait for the piece if it is not downloaded
            while not torrent_handle.have_piece(current_piece):
                if torrent_handle.piece_priority(current_piece) < 7:
                    torrent_handle.piece_priority(current_piece, 7)
                if pieces_per_second:
                    # Pause if the currently played piece is close to the requested piece.
                    addon.log('Currently played piece: {0}'.format(int(pieces_per_second * player.getTime())))
                    proximity = current_piece - player.getTime() * pieces_per_second < 2
                else:
                    proximity = False
                if proximity and not xbmc.getCondVisibility('Player.Paused'):
                    xbmc.executebuiltin('Action(Pause)')
                    paused = True
                    addon.log('serve_file - paused')
                if paused:
                    label.text = addon.get_localized_string(32050).format(current_piece,
                                                                  torrent_handle.status().download_payload_rate / 1024)
                    label.show()
                addon.log('Waiting for piece #{0}...'.format(current_piece))
                time.sleep(0.1)
            if xbmc.getCondVisibility('Player.Paused') and paused:
                xbmc.executebuiltin('Action(Play)')
                paused = False
                addon.log('serve_file - unpaused')
            label.hide()
            # torrent_handle.flush_cache()
            addon.log('Serving piece #{0}'.format(current_piece))
            addon.log('Currently played piece: {0}'.format(int(pieces_per_second * player.getTime())))
            file_.seek(byte_position)
            chunk = file_.read(piece_length)
            if not chunk:
                break
            yield chunk
            byte_position += piece_length


def get_mime(filename):
    """Get mime type for filename"""
    mime = MIME.get(os.path.splitext(filename)[1])
    if mime is None:
        mime = guess_type(filename, False)[0]
    if mime is None:
        mime = 'application/octet-stream'
    return mime
