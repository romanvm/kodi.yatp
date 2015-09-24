# coding: utf-8
# Module: timers
# Created on: 14.07.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

from __future__ import division
import threading
import time
from datetime import datetime, timedelta
from addon import Addon

_addon = Addon()


class Timer(object):
    """
    Timer class

    Implements a repeating timer to call some function in regular intervals.
    """
    def __init__(self, interval, func, *args, **kwargs):
        """
        Class constructor

        @param interval: int - timer interval in seconds
        @param func: a callable function
        @param args: function positional args
        @param kwargs: function kwargs
        """
        self._interval = interval
        self._func = func
        self._abort_flag = threading.Event()
        self._thread = threading.Thread(target=self._runner, args=args, kwargs=kwargs)
        self._thread.daemon = True

    def _runner(self, *args, **kwargs):
        """
        Timed function runner

        @retrun:
        """
        timestamp = time.time()
        while not self._abort_flag.is_set():
            if time.time() - timestamp >= self._interval:
                self._func(*args, **kwargs)
                timestamp = time.time()
            time.sleep(0.2)

    def start(self):
        """
        Timer start

        @retrun:
        """
        self._abort_flag.clear()
        self._thread.start()

    def abort(self):
        """
        Abort timer

        @retrun:
        """
        self._abort_flag.set()
        try:
            self._thread.join()
        except RuntimeError:
            pass


def check_seeding_limits(torrenter):
    """
    Check seding limits

    @param torrenter:
    @retrun:
    """
    for torrent in torrenter.get_all_torrents_info():
        if _addon.ratio_limit:
            try:
                ratio = torrent['total_upload'] / torrent['total_download']
            except ZeroDivisionError:
                ratio = 0
            if _addon.ratio_limit and torrent['state'] == 'seeding' and ratio >= _addon.ratio_limit:
                torrenter.pause_torrent(torrent['info_hash'])
        try:
            if (_addon.time_limit and
                    (datetime.now() - datetime.strptime(torrent['completed_time'], '%Y-%m-%d %H:%M:%S') >=
                         timedelta(hours=_addon.time_limit))):
                if _addon.expired_action == 'pause' and torrent['state'] == 'seeding':
                    torrenter.pause_torrent(torrent['info_hash'])
                elif _addon.expired_action == 1 and torrent['state'] in ('seeding', 'paused'):
                    torrenter.remove_torrent(torrent['info_hash'], _addon.delete_expired_files)
        except ValueError:
            pass


def save_resume_data(torrenter):
    """
    Save torrents resume data

    @param torrenter:
    @retrun:
    """
    torrenter.save_all_resume_data()


def log_torrents(torrenter):
    """
    Log torrents in the torrent session

    @param torrenter:
    @return:
    """
    torrents = torrenter.get_all_torrents_info()
    _addon.log('Torrents:')
    for torrent in torrents:
        _addon.log(str(torrent))
