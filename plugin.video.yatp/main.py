# -*- coding: utf-8 -*-
# Name:        main
# Author:      Roman Miroshnychenko aka Roman V. M.
# Created on:  09.05.2015
# Licence:     GPL v.3: http://www.gnu.org/copyleft/gpl.html
"""
Plugin main module
"""
# Todo: add more logging (buffer_pool, torrent data in a session).
# Todo: improve controlled file serving by checking piece distance.
# Todo: implement hachoir library for dynamic calculating of buffer_length.

from libs.client.actions import plugin

plugin.run()
