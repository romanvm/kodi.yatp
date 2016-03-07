# coding: utf-8
# Module: tests
# Created on: 26.01.2016
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)

import os
import sys
import unittest

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'tests', 'server'))

from tests_timers import *

if __name__ == '__main__':
    unittest.main()
