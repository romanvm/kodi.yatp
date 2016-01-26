# coding: utf-8
# Module: tests_timers
# Created on: 26.01.2016
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)

import sys
import os
import unittest
from datetime import datetime, timedelta
from tests import basedir
from mock import MagicMock


mock_addon = MagicMock()
mock_addon_Addon = MagicMock()
mock_addon.Addon.return_value = mock_addon_Addon
mock_torrenter = MagicMock()

sys.path.append(os.path.join(basedir, 'plugin.video.yatp'))
sys.modules['libs.server.addon'] = mock_addon
from libs.server.timers import check_seeding_limits


class SeedingLimitsTestCase(unittest.TestCase):
    def setUp(self):
        mock_torrenter.reset_mock()
        mock_addon_Addon.ratio_limit = 1.0
        mock_addon_Addon.time_limit = 0
        mock_addon_Addon.delete_expired_files = False
        self.test_info = {
            'info_hash': 'aabbccddeeff',
            'total_download': 100,
            'total_upload': 50,
            'state': 'seeding',
            'completed_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        mock_torrenter.get_all_torrents_info.return_value = [self.test_info]

    def test_check_ratio_limit(self):
        check_seeding_limits(mock_torrenter)
        mock_torrenter.pause_torrent.assert_not_called()
        self.test_info['total_upload'] = 101
        check_seeding_limits(mock_torrenter)
        mock_torrenter.pause_torrent.assert_called_with(self.test_info['info_hash'])

    def test_check_time_limit(self):
        mock_addon_Addon.time_limit = 2
        mock_addon_Addon.expired_action = 0
        self.test_info['total_upload'] = 50
        check_seeding_limits(mock_torrenter)
        mock_torrenter.pause_torrent.assert_not_called()
        mock_torrenter.remove_torrent.assert_not_called()
        self.test_info['completed_time'] = (datetime.now() - timedelta(hours=3)).strftime('%Y-%m-%d %H:%M:%S')
        check_seeding_limits(mock_torrenter)
        mock_torrenter.pause_torrent.assert_called_with(self.test_info['info_hash'])
        mock_addon_Addon.expired_action = 1
        check_seeding_limits(mock_torrenter)
        mock_torrenter.remove_torrent.assert_called_with(self.test_info['info_hash'], False)


if __name__ == '__main__':
    unittest.main()
