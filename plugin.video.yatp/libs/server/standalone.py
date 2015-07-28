# coding: utf-8
# Module: standalone
# Created on: 24.07.2015
# Author: Roman Miroshnychenko aka Roman V.M.
# E-mail: romanvm@yandex.ua

import os
import codecs
import json
from datetime import datetime

DEFAULT_CONFIG = {'config_dir': '.',  # Root dir to store resume data
                  'download_dir': './Download',  # Download dir. Change to your dir if necessary.
                  'ratio_limit': 0.0,
                  'time_limit': 0,
                  'expired_action': 'pause',  # Possible values 'pause' and 'delete'
                  'delete_expired_files': False,
                  'torrent_port': 25333,
                  'server_port': 8668,
                  'pass_protect': False,
                  'login': 'yatp',
                  'password': 'yatp'}


class ConfigParser(object):
    """
    Config parser for standalone torrent server
    """
    def __init__(self):
        self._config = None
        config_file = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        if not os.path.exists(config_file):
            with codecs.open(config_file, 'wb', encoding='utf-8') as file_:
                json.dump(DEFAULT_CONFIG, file_, ensure_ascii=False, indent=2)
            self._config = DEFAULT_CONFIG
        else:
            with codecs.open(config_file, 'rb', encoding='utf-8') as file_:
                self._config = json.load(file_, encoding='utf-8')
        if not os.path.exists(self._config['config_dir']):
            os.mkdir(self._config['config_dir'])

    def log(self, message):
        print '{0}: {1}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'), message)

    @property
    def credentials(self):
        return (self._config['login'], self._config['password'])

    @property
    def path(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

    def __getattr__(self, item):
        return self._config[item]
