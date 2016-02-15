#!/usr/bin/env python
# coding: utf-8
# Module: publish
# Created on: 03.08.2015
# Author: Roman Miroshnychenko aka Roman V.M. (romanvm@yandex.ua)


import os
import sys
import re

ADDON = 'plugin.video.yatp'
basedir = os.path.dirname(os.path.abspath(__file__))
os.chdir(basedir)
os.system('git checkout master')
os.system('git merge develop')
os.system('git push --all')
if '-t' in sys.argv:
    with open(os.path.join(basedir, ADDON, 'addon.xml'), 'rb') as addon_xml:
        version = re.search(r'(?<!xml )version="(.+?)"', addon_xml.read()).group(1)
    os.system('git tag v{0}'.format(version))
    os.system('git push --tags')
os.system('git checkout develop')
